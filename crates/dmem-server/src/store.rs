use dmem_contracts::*;
use dmem_core::{extract, normalize_form, validate_content, validate_title};
use rusqlite::{Connection, OptionalExtension, params};
use serde::{Serialize, de::DeserializeOwned};
use sha2::{Digest, Sha256};
use std::{
    path::Path,
    sync::Mutex,
    time::{SystemTime, UNIX_EPOCH},
};
use uuid::Uuid;

pub struct Store {
    pub(crate) db: Mutex<Connection>,
}
fn internal(_: impl std::fmt::Debug) -> Fault {
    Fault::Internal
}
fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
fn id(prefix: &str) -> String {
    format!("{prefix}_{}", Uuid::new_v4().simple())
}
fn encode<T: Serialize>(v: &T) -> Result<String, Fault> {
    serde_json::to_string(v).map_err(internal)
}
fn decode<T: DeserializeOwned>(s: &str) -> Result<T, Fault> {
    serde_json::from_str(s).map_err(internal)
}
fn load<T: DeserializeOwned>(
    db: &Connection,
    owner: &str,
    kind: &str,
    id: &str,
) -> Result<T, Fault> {
    let s:Option<String>=db.query_row("SELECT payload FROM records WHERE id=?1 AND kind=?2 AND (owner=?3 OR (kind='template' AND owner='@catalog'))",params![id,kind,owner],|r|r.get(0)).optional().map_err(internal)?;
    decode(&s.ok_or(Fault::NotFound)?)
}
pub(crate) fn insert<T: Serialize>(
    db: &Connection,
    owner: &str,
    kind: &str,
    id: &str,
    value: &T,
) -> Result<(), Fault> {
    db.execute(
        "INSERT INTO records(id,owner,kind,version,payload,updated_at) VALUES(?1,?2,?3,1,?4,?5)",
        params![id, owner, kind, encode(value)?, now()],
    )
    .map_err(internal)?;
    Ok(())
}
fn list<T: DeserializeOwned>(db: &Connection, owner: &str, kind: &str) -> Result<Vec<T>, Fault> {
    let mut stmt=db.prepare("SELECT payload FROM records WHERE kind=?1 AND (owner=?2 OR (kind='template' AND owner='@catalog')) ORDER BY updated_at DESC,id").map_err(internal)?;
    let rows = stmt
        .query_map(params![kind, owner], |r| r.get::<_, String>(0))
        .map_err(internal)?;
    rows.map(|r| decode(&r.map_err(internal)?)).collect()
}
pub(crate) fn public_origin(db: &Connection, o: &Origin) -> Result<bool, Fault> {
    if !["CC0-1.0", "CC-BY-4.0"].contains(&o.license.as_str()) {
        return Ok(false);
    }
    db.query_row("SELECT EXISTS(SELECT 1 FROM records WHERE id=?1 AND owner='@catalog' AND kind='template') OR EXISTS(SELECT 1 FROM contributions WHERE public_id=?1)",params![o.template_id],|r|r.get(0)).map_err(internal)
}
fn search_ok(s: &Search) -> Result<(), Fault> {
    if s.q.chars().count() > 200 || s.locale.as_ref().is_some_and(|locale| locale.len() > 35) {
        Err(Fault::InvalidInput)
    } else {
        Ok(())
    }
}
impl Store {
    pub fn open(path: impl AsRef<Path>) -> Result<Self, Fault> {
        let path = path.as_ref();
        let conn = Connection::open(path).map_err(internal)?;
        #[cfg(unix)]
        if path != Path::new(":memory:") {
            use std::os::unix::fs::PermissionsExt;
            // Set the database mode before SQLite creates WAL/shared-memory sidecars.
            std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o600))
                .map_err(internal)?;
            for suffix in ["-wal", "-shm"] {
                let mut sidecar = path.as_os_str().to_owned();
                sidecar.push(suffix);
                if std::path::Path::new(&sidecar).exists() {
                    std::fs::set_permissions(&sidecar, std::fs::Permissions::from_mode(0o600))
                        .map_err(internal)?;
                }
            }
        }
        conn.busy_timeout(std::time::Duration::from_secs(5))
            .map_err(internal)?;
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
            .map_err(internal)?;
        conn.execute_batch(include_str!("../migrations/0001_library.sql"))
            .map_err(internal)?;
        conn.execute_batch(include_str!("../migrations/0002_accounts.sql"))
            .map_err(internal)?;
        conn.execute_batch(include_str!("../migrations/0003_contribution_reviews.sql"))
            .map_err(internal)?;
        conn.execute_batch(include_str!("../migrations/0004_member_profiles.sql"))
            .map_err(internal)?;
        conn.execute_batch(include_str!("../migrations/0005_administrator_email.sql"))
            .map_err(internal)?;
        conn.execute_batch(include_str!("../migrations/0006_web_memory.sql"))
            .map_err(internal)?;
        let s = Self {
            db: Mutex::new(conn),
        };
        s.seed()?;
        Ok(s)
    }
    pub fn templates(&self, owner: &str, search: Search) -> Result<List<Template>, Fault> {
        search_ok(&search)?;
        let db = self.db.lock().map_err(internal)?;
        let q = search.q.to_lowercase();
        let items = list::<Template>(&db, owner, "template")?
            .into_iter()
            .filter(|t| {
                search.family.is_none_or(|f| f == t.form.family)
                    && search.visibility.is_none_or(|v| v == t.visibility)
                    && search
                        .locale
                        .as_ref()
                        .is_none_or(|locale| locale == &t.form.locale)
                    && format!("{} {} {}", t.title, t.summary, t.tags.join(" "))
                        .to_lowercase()
                        .contains(&q)
            })
            .take(MAX_RESULTS)
            .collect();
        Ok(List { items })
    }
    pub fn recall_candidates(&self, owner: &str) -> Result<Vec<Template>, Fault> {
        list::<Template>(&*self.db.lock().map_err(internal)?, owner, "template")
    }
    pub fn template(&self, owner: &str, id: &str) -> Result<Template, Fault> {
        load(&*self.db.lock().map_err(internal)?, owner, "template", id)
    }
    pub fn create_template(&self, owner: &str, input: CreateTemplate) -> Result<Template, Fault> {
        self.create_template_with_web_origin(owner, input, None)
    }
    fn create_template_with_web_origin(
        &self,
        owner: &str,
        input: CreateTemplate,
        web_origin: Option<WebOrigin>,
    ) -> Result<Template, Fault> {
        validate_title(&input.title)?;
        if input.summary.chars().count() > 600
            || input.sections.is_empty()
            || input.sections.len() > 12
            || input
                .sections
                .iter()
                .any(|s| s.trim().is_empty() || s.chars().count() > 60)
            || input.tags.len() > 8
            || input.tags.iter().any(|s| s.chars().count() > 32)
        {
            return Err(Fault::InvalidInput);
        }
        let template = Template {
            id: id("tpl"),
            version: 1,
            title: input.title,
            summary: input.summary,
            form: if let Some(origin) = &web_origin {
                origin.form.clone()
            } else {
                normalize_form(input.form)?
            },
            sections: input.sections,
            tags: input.tags,
            author: "My library".into(),
            license: web_origin
                .as_ref()
                .map(|o| o.license.clone())
                .unwrap_or_else(|| "All rights reserved".into()),
            visibility: Visibility::Private,
            origin: None,
            attributions: vec![],
        };
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        insert(&tx, owner, "template", &template.id, &template)?;
        if let Some(mut value) = web_origin {
            value.record_id = template.id.clone();
            crate::web_store::save_origin(&tx, owner, &value)?;
        }
        tx.commit().map_err(internal)?;
        Ok(template)
    }
    pub fn copy_template(&self, owner: &str, template_id: &str) -> Result<Template, Fault> {
        let mut connection = self.db.lock().map_err(internal)?;
        let db = connection.transaction().map_err(internal)?;
        let original: Template = load(&db, owner, "template", template_id)?;
        if original.visibility == Visibility::Public
            && !["CC0-1.0", "CC-BY-4.0"].contains(&original.license.as_str())
        {
            return Err(Fault::LicenseForbids);
        }
        let mut copy = original.clone();
        let inherited = std::mem::take(&mut copy.attributions);
        for o in inherited {
            if public_origin(&db, &o)? {
                copy.attributions.push(o);
            }
        }
        let mut lineage = Vec::new();
        if let Some(o) = original.origin.clone() {
            if public_origin(&db, &o)? {
                lineage.push(o);
            }
        }
        if original.visibility == Visibility::Public {
            lineage.push(Origin {
                template_id: original.id.clone(),
                version: original.version,
                author: original.author.clone(),
                license: original.license.clone(),
            });
        }
        for attribution in lineage {
            if !copy.attributions.iter().any(|o| {
                o.template_id == attribution.template_id && o.version == attribution.version
            }) {
                copy.attributions.push(attribution);
            }
        }
        if copy.attributions.len() > 16 {
            return Err(Fault::LicenseForbids);
        }
        copy.id = id("tpl");
        copy.version = 1;
        copy.visibility = Visibility::Private;
        copy.origin = Some(Origin {
            template_id: original.id,
            version: original.version,
            author: original.author,
            license: original.license,
        });
        insert(&db, owner, "template", &copy.id, &copy)?;
        crate::web_store::clone_origin(&db, owner, template_id, &copy.id)?;
        db.commit().map_err(internal)?;
        Ok(copy)
    }
    pub fn import_source(
        &self,
        owner: &str,
        title: String,
        filename: String,
        bytes: Vec<u8>,
    ) -> Result<Source, Fault> {
        validate_title(&title)?;
        if filename.len() > 180
            || filename.contains(['/', '\\'])
            || filename.chars().any(|c| c.is_control())
        {
            return Err(Fault::InvalidInput);
        }
        let extracted = extract(&filename, &bytes)?;
        let source = Source {
            id: id("src"),
            version: 1,
            title,
            filename,
            format: extracted.format,
            checksum: format!("{:x}", Sha256::digest(&bytes)),
            spans: extracted.spans,
        };
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        insert(&tx, owner, "source", &source.id, &source)?;
        tx.execute(
            "INSERT INTO source_files(source_id,original) VALUES(?1,?2)",
            params![source.id, bytes],
        )
        .map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok(source)
    }
    pub fn sources(&self, owner: &str, search: Search) -> Result<List<Source>, Fault> {
        search_ok(&search)?;
        let db = self.db.lock().map_err(internal)?;
        let q = search.q.to_lowercase();
        Ok(List {
            items: list::<Source>(&db, owner, "source")?
                .into_iter()
                .filter(|s| {
                    s.title.to_lowercase().contains(&q)
                        || s.spans.iter().any(|p| p.text.to_lowercase().contains(&q))
                })
                .take(MAX_RESULTS)
                .collect(),
        })
    }
    pub fn source(&self, owner: &str, id: &str) -> Result<Source, Fault> {
        load(&*self.db.lock().map_err(internal)?, owner, "source", id)
    }
    pub fn source_file(&self, owner: &str, id: &str) -> Result<(Source, Vec<u8>), Fault> {
        let db = self.db.lock().map_err(internal)?;
        let source = load(&db, owner, "source", id)?;
        let bytes = db
            .query_row(
                "SELECT original FROM source_files WHERE source_id=?1",
                [id],
                |r| r.get(0),
            )
            .map_err(internal)?;
        Ok((source, bytes))
    }
    pub fn template_from_source(&self, owner: &str, source_id: &str) -> Result<Template, Fault> {
        let (source, bytes) = self.source_file(owner, source_id)?;
        let extracted = extract(&source.filename, &bytes)?;
        let deck = source.format == "pptx";
        let mut sections: Vec<String> = if deck {
            extracted.slides.iter().map(|s| s.title.clone()).collect()
        } else {
            extracted
                .blocks
                .iter()
                .filter_map(|b| {
                    if let Block::Heading { text, .. } = b {
                        Some(text.clone())
                    } else {
                        None
                    }
                })
                .collect()
        };
        if sections.is_empty() {
            sections = source
                .spans
                .iter()
                .take(12)
                .map(|s| s.text.chars().take(60).collect())
                .collect()
        }
        sections.truncate(12);
        for s in &mut sections {
            *s = s.chars().take(60).collect()
        }
        let web_origin = match self.web_origin(owner, source_id) {
            Ok(value) => Some(value),
            Err(Fault::NotFound) => None,
            Err(e) => return Err(e),
        };
        self.create_template_with_web_origin(
            owner,
            CreateTemplate {
                title: source.title,
                summary: "Structure extracted from my file".into(),
                form: FormInput {
                    provider: source.format,
                    doc_type: if deck { "report_deck" } else { "report" }.into(),
                    locale: "en-US".into(),
                    region: None,
                    variant: None,
                    page: None,
                },
                sections,
                tags: vec!["Imported template".into()],
            },
            web_origin,
        )
    }
    pub fn create_document(&self, owner: &str, input: CreateDocument) -> Result<Document, Fault> {
        validate_title(&input.title)?;
        if input.source_ids.len() > 10 {
            return Err(Fault::InvalidInput);
        }
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let template: Template = load(&tx, owner, "template", &input.template_id)?;
        if template.form.family == Family::Sheet {
            return Err(Fault::UnsupportedFormat);
        }
        if template.form.family == Family::Deck && !input.outline_approved {
            return Err(Fault::InvalidInput);
        }
        let mut refs = Vec::new();
        let mut evidence = Vec::new();
        for source_id in input.source_ids {
            if refs
                .iter()
                .any(|r: &SourceVersion| r.source_id == source_id)
            {
                continue;
            }
            let source: Source = load(&tx, owner, "source", &source_id)?;
            refs.push(SourceVersion {
                source_id: source.id.clone(),
                version: source.version,
                title: source.title.clone(),
            });
            for span in source.spans.iter().take(3) {
                evidence.push((
                    source.title.clone(),
                    span.text.chars().take(2000).collect::<String>(),
                    Citation {
                        source_id: source.id.clone(),
                        source_version: source.version,
                        span_id: span.id.clone(),
                    },
                ))
            }
        }
        let korean = template.form.locale.starts_with("ko");
        let confirmation = if korean {
            "확인 필요"
        } else {
            "Needs confirmation"
        };
        let evidence_label = if korean { "근거" } else { "Evidence" };
        let source_heading = if korean {
            "선택한 참고자료 원문"
        } else {
            "Selected Source Excerpts"
        };
        let mut content = Content::default();
        if template.form.family == Family::Deck {
            for section in &template.sections {
                content.slides.push(Slide {
                    title: section.clone(),
                    body: format!("{{{{{confirmation}: {section}}}}}"),
                    citations: vec![],
                })
            }
            for (title, text, citation) in evidence {
                content.slides.push(Slide {
                    title: format!(
                        "{evidence_label}: {}",
                        title.chars().take(60).collect::<String>()
                    ),
                    body: text,
                    citations: vec![citation],
                })
            }
        } else {
            for section in &template.sections {
                content.blocks.push(Block::Heading {
                    text: section.clone(),
                    level: 2,
                });
                content.blocks.push(Block::Paragraph {
                    text: format!("{{{{{confirmation}: {section}}}}}"),
                })
            }
            if !evidence.is_empty() {
                content.blocks.push(Block::Heading {
                    text: source_heading.into(),
                    level: 2,
                })
            }
            for (_, text, citation) in evidence {
                content.blocks.push(Block::Quote {
                    text,
                    citation: Some(citation),
                })
            }
        }
        validate_content(template.form.family, &content)?;
        let doc = Document {
            id: id("doc"),
            version: 1,
            title: input.title,
            family: template.form.family,
            template: Origin {
                template_id: template.id,
                version: template.version,
                author: template.author,
                license: template.license,
            },
            source_versions: refs,
            content,
            created_at: now(),
            updated_at: now(),
        };
        insert(&tx, owner, "document", &doc.id, &doc)?;
        tx.execute(
            "INSERT INTO revisions(document_id,owner,version,payload) VALUES(?1,?2,1,?3)",
            params![doc.id, owner, encode(&doc)?],
        )
        .map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok(doc)
    }
    pub fn documents(&self, owner: &str, search: Search) -> Result<List<Document>, Fault> {
        search_ok(&search)?;
        let db = self.db.lock().map_err(internal)?;
        let q = search.q.to_lowercase();
        Ok(List {
            items: list::<Document>(&db, owner, "document")?
                .into_iter()
                .filter(|d| {
                    search.family.is_none_or(|f| f == d.family)
                        && d.title.to_lowercase().contains(&q)
                })
                .take(MAX_RESULTS)
                .collect(),
        })
    }
    pub fn document(&self, owner: &str, id: &str) -> Result<Document, Fault> {
        load(&*self.db.lock().map_err(internal)?, owner, "document", id)
    }
    pub fn revisions(&self, owner: &str, id: &str) -> Result<List<Document>, Fault> {
        let db = self.db.lock().map_err(internal)?;
        let _: Document = load(&db, owner, "document", id)?;
        let mut stmt=db.prepare("SELECT payload FROM revisions WHERE document_id=?1 AND owner=?2 ORDER BY version DESC").map_err(internal)?;
        let rows = stmt
            .query_map(params![id, owner], |r| r.get::<_, String>(0))
            .map_err(internal)?;
        Ok(List {
            items: rows
                .map(|r| decode(&r.map_err(internal)?))
                .collect::<Result<_, _>>()?,
        })
    }
    pub fn save_document(
        &self,
        owner: &str,
        id: &str,
        input: SaveDocument,
    ) -> Result<Document, Fault> {
        validate_title(&input.title)?;
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let mut doc: Document = load(&tx, owner, "document", id)?;
        if doc.version != input.base_version {
            return Err(Fault::VersionConflict);
        }
        validate_content(doc.family, &input.content)?;
        let check =
            |citation: &Citation, text: Option<&str>| -> Result<(), Fault> {
                if !doc.source_versions.iter().any(|r| {
                    r.source_id == citation.source_id && r.version == citation.source_version
                }) {
                    return Err(Fault::InvalidInput);
                }
                let source: Source = load(&tx, owner, "source", &citation.source_id)?;
                let span = source
                    .spans
                    .iter()
                    .find(|s| s.id == citation.span_id)
                    .ok_or(Fault::InvalidInput)?;
                if text.is_some_and(|t| t.is_empty() || !span.text.starts_with(t)) {
                    return Err(Fault::InvalidInput);
                }
                Ok(())
            };
        for b in &input.content.blocks {
            if let Block::Quote {
                text,
                citation: Some(c),
            } = b
            {
                check(c, Some(text))?
            }
        }
        for s in &input.content.slides {
            for c in &s.citations {
                check(c, None)?
            }
        }
        doc.version = doc.version.checked_add(1).ok_or(Fault::Internal)?;
        doc.title = input.title;
        doc.content = input.content;
        doc.updated_at = now();
        tx.execute(
            "UPDATE records SET version=?1,payload=?2,updated_at=?3 WHERE id=?4 AND owner=?5",
            params![doc.version, encode(&doc)?, doc.updated_at, id, owner],
        )
        .map_err(internal)?;
        tx.execute(
            "INSERT INTO revisions(document_id,owner,version,payload) VALUES(?1,?2,?3,?4)",
            params![id, owner, doc.version, encode(&doc)?],
        )
        .map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok(doc)
    }
    fn seed(&self) -> Result<(), Fault> {
        let seeds = [
            (
                "worklog.daily.ko",
                "일일 업무일지",
                "하루의 우선순위와 실행 결과를 정리하세요.",
                "report",
                "docx",
                vec![
                    "날짜와 작성자",
                    "오늘의 우선순위",
                    "완료한 일",
                    "진행 중인 일",
                    "막힘과 도움 요청",
                    "다음 할 일",
                ],
                vec!["업무 기록", "P0"],
            ),
            (
                "meeting.minutes.ko",
                "회의록과 액션아이템",
                "논의를 결정과 실행으로 연결하는 회의록.",
                "meeting_minutes",
                "docx",
                vec![
                    "회의 목적",
                    "날짜와 참석자",
                    "안건",
                    "논의 요약",
                    "결정 사항",
                    "액션아이템 · 담당자 · 기한",
                    "후속 일정",
                ],
                vec!["회의와 프로젝트", "P0"],
            ),
            (
                "report.weekly.ko",
                "주간 업무보고",
                "성과, 진행 상황, 다음 주의 계획을 한눈에.",
                "report",
                "docx",
                vec![
                    "기간과 핵심 요약",
                    "완료 결과",
                    "목표 대비 지표",
                    "진행 중인 일",
                    "리스크와 요청",
                    "다음 주 계획",
                ],
                vec!["업무 기록", "P0"],
            ),
            (
                "sales.quote.ko",
                "견적서",
                "범위와 가격, 조건을 명확히 전하는 견적.",
                "quote",
                "docx",
                vec![
                    "공급자와 고객",
                    "견적 번호와 일자",
                    "품목 · 수량 · 단가 · 금액",
                    "공급가와 세금",
                    "유효기간과 납기",
                    "결제 조건",
                ],
                vec!["영업과 사업", "P0"],
            ),
            (
                "business.proposal.ko",
                "사업 제안서",
                "고객의 과제에서 산출물과 성공 기준까지.",
                "proposal",
                "docx",
                vec![
                    "요약",
                    "고객의 과제",
                    "제안 접근법",
                    "범위와 산출물",
                    "일정과 가격",
                    "성공 기준",
                    "다음 단계",
                ],
                vec!["영업과 사업", "P0"],
            ),
            (
                "career.resume.ko",
                "이력서 / CV",
                "경력과 프로젝트를 성과 중심으로 정리하세요.",
                "resume",
                "docx",
                vec![
                    "이름과 연락처",
                    "지원 직무와 요약",
                    "경력과 성과",
                    "프로젝트",
                    "학력",
                    "기술과 자격",
                ],
                vec!["인사", "P0"],
            ),
            (
                "startup.pitch.ko",
                "스타트업 피치덱",
                "문제에서 제품, 비즈니스와 다음 요청까지.",
                "pitch_deck",
                "pptx",
                vec![
                    "표지",
                    "문제",
                    "해결책",
                    "제품",
                    "시장",
                    "비즈니스 모델",
                    "트랙션",
                    "GTM",
                    "경쟁과 방어력",
                    "팀",
                    "재무와 요청",
                ],
                vec!["프레젠테이션", "P0"],
            ),
            (
                "project.review.ko",
                "프로젝트 리뷰",
                "목표와 결과를 함께 살펴보는 프로젝트 덱.",
                "report_deck",
                "pptx",
                vec![
                    "목표",
                    "전체 상태",
                    "핵심 지표",
                    "마일스톤",
                    "성과와 미달",
                    "리스크",
                    "결정 요청",
                    "다음 계획",
                ],
                vec!["프레젠테이션", "P1"],
            ),
            (
                "budget.sheet.ko",
                "예산·경비 관리",
                "시트 구조 미리보기 · 편집기는 준비 중입니다.",
                "budget_sheet",
                "xlsx",
                vec!["날짜", "항목", "예산", "실적", "증빙", "차액"],
                vec!["스프레드시트", "후속"],
            ),
        ];
        let english_seeds = [
            (
                "worklog.daily.en",
                "Daily Work Log",
                "Keep daily priorities, progress, and next steps together.",
                "report",
                "docx",
                vec![
                    "Date and Owner",
                    "Today's Priorities",
                    "Completed Work",
                    "Work in Progress",
                    "Blockers and Support",
                    "Next Steps",
                ],
                vec!["Work", "Starter"],
            ),
            (
                "meeting.minutes.en",
                "Meeting Notes and Action Items",
                "Turn discussion into clear decisions and next steps.",
                "meeting_minutes",
                "docx",
                vec![
                    "Purpose",
                    "Date and Participants",
                    "Agenda",
                    "Discussion Summary",
                    "Decisions",
                    "Action Items, Owners, and Due Dates",
                    "Follow-up",
                ],
                vec!["Meetings", "Starter"],
            ),
            (
                "report.weekly.en",
                "Weekly Status Report",
                "Share progress, results, and the plan for next week.",
                "report",
                "docx",
                vec![
                    "Period and Summary",
                    "Completed Work",
                    "Metrics Against Goals",
                    "Work in Progress",
                    "Risks and Requests",
                    "Next Week",
                ],
                vec!["Work", "Starter"],
            ),
            (
                "sales.quote.en",
                "Sales Quote",
                "Make scope, pricing, and terms clear.",
                "quote",
                "docx",
                vec![
                    "Supplier and Customer",
                    "Quote Number and Date",
                    "Items, Quantities, and Prices",
                    "Subtotal and Tax",
                    "Validity and Delivery",
                    "Payment Terms",
                ],
                vec!["Sales", "Starter"],
            ),
            (
                "business.proposal.en",
                "Business Proposal",
                "Connect the customer's needs to deliverables and success criteria.",
                "proposal",
                "docx",
                vec![
                    "Executive Summary",
                    "Customer Needs",
                    "Proposed Approach",
                    "Scope and Deliverables",
                    "Timeline and Pricing",
                    "Success Criteria",
                    "Next Steps",
                ],
                vec!["Business", "Starter"],
            ),
            (
                "career.resume.en",
                "Resume / CV",
                "Present your experience and projects through their outcomes.",
                "resume",
                "docx",
                vec![
                    "Name and Contact Details",
                    "Role and Summary",
                    "Experience and Achievements",
                    "Projects",
                    "Education",
                    "Skills and Qualifications",
                ],
                vec!["Career", "Starter"],
            ),
            (
                "startup.pitch.en",
                "Startup Pitch Deck",
                "Build a clear story from the problem to your next ask.",
                "pitch_deck",
                "pptx",
                vec![
                    "Cover",
                    "Problem",
                    "Solution",
                    "Product",
                    "Market",
                    "Business Model",
                    "Traction",
                    "Go-to-Market",
                    "Competition and Advantage",
                    "Team",
                    "Financials and Ask",
                ],
                vec!["Presentations", "Starter"],
            ),
            (
                "project.review.en",
                "Project Review",
                "Review goals, outcomes, and decisions in one focused deck.",
                "report_deck",
                "pptx",
                vec![
                    "Goals",
                    "Overall Status",
                    "Key Metrics",
                    "Milestones",
                    "Results and Gaps",
                    "Risks",
                    "Decisions Needed",
                    "Next Steps",
                ],
                vec!["Presentations", "Starter"],
            ),
            (
                "budget.sheet.en",
                "Budget and Expenses",
                "Preview a spreadsheet structure. Spreadsheet editing is planned.",
                "budget_sheet",
                "xlsx",
                vec!["Date", "Item", "Budget", "Actual", "Receipt", "Variance"],
                vec!["Spreadsheets", "Preview"],
            ),
        ];
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        for ((id, title, summary, doc_type, provider, sections, tags), locale) in seeds
            .into_iter()
            .map(|seed| (seed, "ko-KR"))
            .chain(english_seeds.into_iter().map(|seed| (seed, "en-US")))
        {
            let t = Template {
                id: id.into(),
                version: 1,
                title: title.into(),
                summary: summary.into(),
                form: normalize_form(FormInput {
                    provider: provider.into(),
                    doc_type: doc_type.into(),
                    locale: locale.into(),
                    region: None,
                    variant: None,
                    page: None,
                })?,
                tags: tags.into_iter().map(str::to_owned).collect(),
                sections: sections.into_iter().map(str::to_owned).collect(),
                author: "My Document Memory".into(),
                license: "CC0-1.0".into(),
                visibility: Visibility::Public,
                origin: None,
                attributions: vec![],
            };
            tx.execute("INSERT OR IGNORE INTO records(id,owner,kind,version,payload,updated_at) VALUES(?1,'@catalog','template',1,?2,0)",params![id,encode(&t)?]).map_err(internal)?;
        }
        crate::starter::insert(&tx)?;
        tx.commit().map_err(internal)?;
        Ok(())
    }
}
