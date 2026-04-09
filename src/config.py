from pydantic import BaseModel, Field


class GeneralConfig(BaseModel):
    project_name: str = "My PM Project"
    output_dir: str = "output"
    raw_dir: str = "raw"
    processed_dir: str = "processed"
    log_level: str = "INFO"


class ConfluenceConfig(BaseModel):
    enabled: bool = False
    base_url: str = ""
    spaces: list[dict] = Field(default_factory=list)
    pinned_page_ids: list[str] = Field(default_factory=list)
    export_format: str = "storage"
    max_pages_per_space: int = 200


class GitHubConfig(BaseModel):
    enabled: bool = False
    repos: list[dict] = Field(default_factory=list)


class WebexConfig(BaseModel):
    enabled: bool = False
    meeting_ids: list[str] = Field(default_factory=list)
    room_ids: list[str] = Field(default_factory=list)
    lookback_days: int = 30


class SourcesConfig(BaseModel):
    confluence: ConfluenceConfig | None = None
    github: GitHubConfig | None = None
    webex: WebexConfig | None = None


class MarkdownConfig(BaseModel):
    wrap_width: int = 0
    heading_style: str = "atx"
    bullet_char: str = "-"


class TranslatorConfig(BaseModel):
    pdf_engine: str = "pdfplumber"
    pdf_strip_patterns: list[str] = Field(default_factory=list)
    markdown: MarkdownConfig = Field(default_factory=MarkdownConfig)


class ChangelogConfig(BaseModel):
    group_by: str = "source"
    max_entries: int = 500


class EngineConfig(BaseModel):
    ticket_patterns: list[str] = Field(default_factory=list)
    decision_keywords: list[str] = Field(default_factory=list)
    changelog: ChangelogConfig = Field(default_factory=ChangelogConfig)


class PublisherConfig(BaseModel):
    generate_context: bool = True
    add_frontmatter: bool = True


class PipelineConfig(BaseModel):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    translator: TranslatorConfig = Field(default_factory=TranslatorConfig)
    engine: EngineConfig = Field(default_factory=EngineConfig)
    publisher: PublisherConfig = Field(default_factory=PublisherConfig)
