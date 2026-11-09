#![forbid(unsafe_code)]
mod formats;
mod normalization;
mod output;
mod recall;
pub mod review;
pub mod web;
use dmem_contracts::*;
pub use formats::{Extracted, extract};
pub use normalization::*;
pub use output::{Export, export};
pub use recall::recall;

pub fn validate_title(title: &str) -> Result<(), Fault> {
    if title.trim().is_empty()
        || title.chars().count() > 120
        || title.chars().any(|c| c.is_control())
    {
        return Err(Fault::InvalidInput);
    }
    Ok(())
}
pub fn validate_content(family: Family, c: &Content) -> Result<(), Fault> {
    let size = serde_json::to_vec(c)
        .map_err(|_| Fault::InvalidInput)?
        .len();
    if size > MAX_CONTENT {
        return Err(Fault::PayloadTooLarge);
    }
    match family {
        Family::Document if c.blocks.is_empty() || !c.slides.is_empty() || c.blocks.len() > 500 => {
            return Err(Fault::InvalidInput);
        }
        Family::Deck if c.slides.is_empty() || !c.blocks.is_empty() || c.slides.len() > 100 => {
            return Err(Fault::InvalidInput);
        }
        Family::Sheet => return Err(Fault::UnsupportedFormat),
        _ => {}
    }
    for b in &c.blocks {
        match b {
            Block::Heading { level, .. } if !(1..=6).contains(level) => {
                return Err(Fault::InvalidInput);
            }
            Block::List { items } if items.len() > 200 => return Err(Fault::InvalidInput),
            Block::Table { rows } if rows.len() > 200 || rows.iter().any(|r| r.len() > 30) => {
                return Err(Fault::InvalidInput);
            }
            _ => {}
        }
    }
    for s in &c.slides {
        validate_title(&s.title)?;
        if s.body.chars().count() > 10000 {
            return Err(Fault::InvalidInput);
        }
    }
    Ok(())
}
