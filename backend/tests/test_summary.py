
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from types import SimpleNamespace

import pytest

from app.core.database import Base
from app.models.document import Document
from app.schemas.summary_schema import ResearchSummary
from app.ai.summary_generator import SummaryGenerator
from app.services.summary_service import SummaryService

import app.models


class FakeSummaryGenerator:

    def __init__(self):
        self.call_count = 0

    def generate(self, markdown: str) -> ResearchSummary:

        self.call_count += 1

        return ResearchSummary(
            title="Machine Learning Research",
            authors=["John Smith", "Jane Doe"],
            abstract="A study about machine learning.",
            problem_statement="Existing methods do not address this research problem.",
            methodology="Experimental evaluation.",
            key_result=[
                "The proposed model showed improvements."
            ],
            conclusion="The approach was effective."
        )


@pytest.mark.parametrize("portions", [
    ["Short paper content"],
    ["First section", "Second section"],
])
def test_summary_generator_handles_short_and_long_documents(portions):
    expected_summary = ResearchSummary(
        title="Research Paper",
        authors=["Jane Doe"],
        abstract="Research problem",
        problem_statement="Existing approaches leave a research gap.",
        methodology="Experiment",
        key_result=["Result"],
        conclusion="Conclusion",
    )

    class FakeStructuredModel:
        def invoke(self, messages, config=None):
            assert messages[1][0] == "human"
            if len(portions) == 2:
                assert "Notes for First section" in messages[1][1]
                assert "Notes for Second section" in messages[1][1]
            else:
                assert portions[0] in messages[1][1]
            return expected_summary

    class FakeChatModel:
        def __init__(self):
            self.note_calls = 0

        def invoke(self, messages, config=None):
            self.note_calls += 1
            return SimpleNamespace(content=f"Notes for {portions[self.note_calls - 1]}")

        def with_structured_output(self, schema, method):
            assert schema is ResearchSummary
            assert method == "json_schema"
            return FakeStructuredModel()

    model = FakeChatModel()
    generator = SummaryGenerator(model=model)
    generator.splitter = SimpleNamespace(split_text=lambda _: portions)

    assert generator.generate("Paper content") == expected_summary
    assert model.note_calls == (0 if len(portions) == 1 else 2)


def test_summary_generation(tmp_path):

    database_path = tmp_path / "test.db"

    engine = create_engine(
        f"sqlite:///{database_path}"
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    document_id = "test-paper"

    extracted_directory = tmp_path / "extracted"

    document_directory = (
        extracted_directory / document_id
    )

    document_directory.mkdir(parents=True)

    markdown_path = document_directory / "document.md"

    markdown_path.write_text(
        "# Machine Learning Research\n\n"
        "The researchers evaluated a new model.",
        encoding="utf-8"
    )

    with TestingSession() as database:

        document = Document(
            id=document_id,
            filename="research.pdf",
            file_path=str(tmp_path / "research.pdf"),
            status="indexed"
        )

        database.add(document)
        database.commit()

        fake_generator = FakeSummaryGenerator()

        service = SummaryService(
            database=database,
            summary_generator=fake_generator,
            extracted_directory=extracted_directory
        )

        # Generate the summary.
        summary = service.generate_summary(document_id)

        assert summary.title == "Machine Learning Research"

        database.refresh(document)

        assert document.status == "completed"
        assert document.summary_json is not None

        # Retrieve the saved summary.
        saved_summary = service.get_summary(document_id)

        assert saved_summary is not None
        assert saved_summary.title == summary.title
        assert saved_summary.problem_statement == summary.problem_statement

        # Generating again should reuse SQLite data.
        second_summary = service.generate_summary(
            document_id
        )

        assert second_summary.title == summary.title
        assert fake_generator.call_count == 1

        # Older saved summaries remain readable without inventing a statement.
        legacy_document = Document(
            id="legacy-paper",
            filename="legacy.pdf",
            file_path=str(tmp_path / "legacy.pdf"),
            status="completed",
            summary_json=summary.model_dump_json(exclude={"problem_statement"}),
        )
        database.add(legacy_document)
        database.commit()
        legacy_summary = service.get_summary(legacy_document.id)
        assert legacy_summary is not None
        assert legacy_summary.problem_statement.startswith("Not available")
        assert service.generate_summary(legacy_document.id) == legacy_summary
        assert fake_generator.call_count == 1

    engine.dispose()
