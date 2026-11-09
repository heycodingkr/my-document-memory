use dmem_client::DmemClient;
use dmem_mcp::{FrameError, handle, parse_error, read_frame};
use tokio::io::{AsyncWriteExt, BufReader};
#[tokio::main]
async fn main() {
    if let Err(e) = run().await {
        eprintln!("dmem-mcp: {e}");
        std::process::exit(1)
    }
}
async fn run() -> Result<(), Box<dyn std::error::Error>> {
    let base = std::env::var("DMEM_URL").unwrap_or_else(|_| "http://127.0.0.1:3847".into());
    let token = std::env::var("DMEM_TOKEN").map_err(|_| "auth_required")?;
    let client = DmemClient::new(&base, token)?;
    let mut reader = BufReader::new(tokio::io::stdin());
    let mut out = tokio::io::stdout();
    loop {
        let result = match read_frame(&mut reader).await {
            Ok(None) => break,
            Err(FrameError::TooLarge) => Some(parse_error()),
            Err(FrameError::Io) => return Err("server_unavailable".into()),
            Ok(Some(line)) => match serde_json::from_slice(&line) {
                Ok(message) => handle(&client, message).await,
                Err(_) => Some(parse_error()),
            },
        };
        if let Some(result) = result {
            let mut bytes = serde_json::to_vec(&result)?;
            bytes.push(b'\n');
            out.write_all(&bytes).await?;
            out.flush().await?
        }
    }
    Ok(())
}
