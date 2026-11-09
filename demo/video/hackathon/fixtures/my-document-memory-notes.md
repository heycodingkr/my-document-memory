# My Document Memory: project notes

My Document Memory helps people share how documents are made, so anyone can create the document they need with AI.
It stores three things separately: templates, references, and finished documents.
A template holds the sections of a document or the outline of a deck, with its author, version, and license.
A reference is an uploaded file kept with its original, a SHA-256 checksum, and the extracted text with positions.
A finished document records which template and reference versions it used, links its evidence to the source, and keeps every saved version.
The runtime is a Rust API with SQLite storage, a web app, a dmem command line, and a stdio MCP server with seven tools.
An AI host such as Arise Browser can search templates and references through MCP and create an editable draft.
Facts that are not in the references stay marked as needing confirmation instead of being invented.
Documents can be exported to DOCX, PPTX, Markdown, and HTML; PDF uses the browser's print function.
Today the public catalog is a set of built-in templates that can be copied into a private library with the original author and license kept.
Wider sharing between people, such as publishing templates and team libraries, and writing directly inside Google Docs, Slides, and Notion are planned next.
