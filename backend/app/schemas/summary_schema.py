from pydantic import BaseModel, Field

class ResearchSummary(BaseModel):
    
    title : str = Field(
        description = "Title of the research paper"
    )
    
    authors : list[str] = Field(
        description="Authors of the research paper"
    )
    
    abstract : str = Field(
        description = "Abstract of the research paper"
    ) 

    problem_statement : str = Field(
        description="Specific research problem, gap, or limitation addressed by the paper"
    )
    
    methodology : str = Field(
        description="Research methods and experimental approach"
    )
    
    key_result : list[str] = Field(
        description="Important findings from the study"
    )
    
    conclusion : str = Field(
        description="Overall conclusion of the research"
    )
