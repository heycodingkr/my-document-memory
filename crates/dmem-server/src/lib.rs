#![forbid(unsafe_code)]
mod administrator;
mod community;
mod http;
mod identity;
mod members;
mod starter;
mod store;
mod web;
mod web_store;
pub use http::{router, router_with_auth, router_with_services};
pub use web::WebConfig;
pub use identity::{AuthConfig, Delivery, EmailSender, ResendEmailSender};
pub use store::Store;
