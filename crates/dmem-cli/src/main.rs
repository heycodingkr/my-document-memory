use clap::{Parser, Subcommand};
use dmem_client::{DmemClient, safe_id, search_path};
use serde_json::{Value, json};
#[derive(Parser)]
#[command(name = "dmem", about = "My Document Memory local client")]
struct Args {
    #[arg(long, env = "DMEM_URL", default_value = "http://127.0.0.1:3847")]
    url: String,
    #[arg(long, env = "DMEM_TOKEN", hide_env_values = true)]
    token: String,
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    Status,
    Templates {
        #[arg(default_value = "")]
        query: String,
    },
    Sources {
        #[arg(default_value = "")]
        query: String,
    },
    Documents {
        #[arg(default_value = "")]
        query: String,
    },
    Copy {
        template_id: String,
    },
    Import {
        file: std::path::PathBuf,
        #[arg(long)]
        title: Option<String>,
    },
    Create {
        template_id: String,
        #[arg(long)]
        title: String,
        #[arg(long)]
        source: Vec<String>,
        #[arg(long)]
        approve_outline: bool,
    },
    Show {
        document_id: String,
    },
    Export {
        document_id: String,
        #[arg(long)]
        format: String,
        #[arg(long)]
        output: std::path::PathBuf,
    },
}
#[tokio::main]
async fn main() {
    if let Err(e) = run().await {
        eprintln!("dmem: {e}");
        std::process::exit(1)
    }
}
async fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let client = DmemClient::new(&args.url, args.token)?;
    let check = |id: &str| -> Result<(), Box<dyn std::error::Error>> {
        if safe_id(id) {
            Ok(())
        } else {
            Err("invalid_input".into())
        }
    };
    let value: Value = match args.command {
        Command::Status => client.get("/v1/status").await?,
        Command::Templates { query } => client.get(&search_path("templates", &query)).await?,
        Command::Sources { query } => client.get(&search_path("sources", &query)).await?,
        Command::Documents { query } => client.get(&search_path("documents", &query)).await?,
        Command::Copy { template_id } => {
            check(&template_id)?;
            client
                .post(&format!("/v1/templates/{template_id}/copy"), &json!({}))
                .await?
        }
        Command::Import { file, title } => {
            let name = file
                .file_name()
                .and_then(|s| s.to_str())
                .ok_or("invalid_input")?
                .to_owned();
            if std::fs::metadata(&file)?.len() > dmem_contracts::MAX_UPLOAD as u64 {
                return Err("payload_too_large".into());
            }
            client
                .upload(
                    title.unwrap_or_else(|| name.chars().take(120).collect()),
                    name,
                    std::fs::read(file)?,
                )
                .await?
        }
        Command::Create {
            template_id,
            title,
            source,
            approve_outline,
        } => {
            check(&template_id)?;
            for s in &source {
                check(s)?
            }
            client.post("/v1/documents",&json!({"template_id":template_id,"title":title,"source_ids":source,"outline_approved":approve_outline})).await?
        }
        Command::Show { document_id } => {
            check(&document_id)?;
            client.get(&format!("/v1/documents/{document_id}")).await?
        }
        Command::Export {
            document_id,
            format,
            output,
        } => {
            check(&document_id)?;
            if !["md", "html", "docx", "pptx"].contains(&format.as_str()) {
                return Err("unsupported_format".into());
            }
            let bytes = client
                .download(&format!("/v1/documents/{document_id}/export/{format}"))
                .await?;
            // create_new prevents accidentally replacing a user's existing file.
            use std::io::Write;
            let mut f = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(output)?;
            f.write_all(&bytes)?;
            json!({"exported":true,"bytes":bytes.len()})
        }
    };
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}
