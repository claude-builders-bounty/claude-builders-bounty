use crate::openclaw::OpenClaw;
use crate::subcommands::conversation::Conversation;
use clap::Parser;
use std::process;

/// Subcommand to view and continue Claude AI conversations
#[derive(Parser, Debug)]
#[command(
    name = "claude",
    about = "View and continue Claude AI conversations",
    long_about = None,
    example = "openclaw claude                    # List all conversations
openclaw claude --limit 20        # List up to 20 conversations
openclaw claude --id abc123        # View specific conversation"
)]
pub struct Cli {
    /// Conversation ID to view (if not provided, shows list)
    #[arg(short, long)]
    id: Option<String>,

    /// Maximum number of conversations to display (default: 10)
    #[arg(short, long, default_value_t = 10)]
    limit: usize,
}

impl Cli {
    pub fn run(&self, openclaw: &OpenClaw) -> process::ExitCode {
        // If conversation ID is provided, show that conversation
        if let Some(id) = &self.id {
            match Self::show_conversation(openclaw, id) {
                Ok(_) => process::ExitCode::SUCCESS,
                Err(e) => {
                    eprintln!("Error showing conversation: {}", e);
                    process::ExitCode::FAILURE
                }
            }
        } else {
            // Show list of conversations
            match Self::list_conversations(openclaw) {
                Ok(_) => process::ExitCode::SUCCESS,
                Err(e) => {
                    eprintln!("Error listing conversations: {}", e);
                    process::ExitCode::FAILURE
                }
            }
        }
    }

    /// List all conversations with summaries
    fn list_conversations(openclaw: &OpenClaw) -> Result<(), Box<dyn std::error::Error>> {
        let conversations: Vec<Conversation> = openclaw.list_conversations(self.limit)?;

        if conversations.is_empty() {
            println!("No conversations found. Start a new conversation with:");
            println!("  openclaw chat");
            return Ok(());
        }

        // Display header
        println!();
        println!("Your Claude AI Conversations");
        println!("{}", "═".repeat(80));
        println!();

        // Display conversations in a formatted table
        println!(
            "{:<8} {:<20} {:<10} {}",
            "ID", "Created", "Messages", "First Message Preview"
        );
        println!("{}", "─".repeat(80));

        for conv in &conversations {
            let first_msg = conv
                .first_message
                .as_deref()
                .unwrap_or("(no messages)")
                .chars()
                .take(45)
                .collect::<String>();
            let created = conv.created_at.format("%Y-%m-%d %H:%M").to_string();

            // Truncate ID for display (show first 8 chars)
            let display_id = if conv.id.len() > 8 {
                conv.id[..8].to_string()
            } else {
                conv.id.clone()
            };

            println!(
                "{:<8} {:<20} {:<10} {}",
                display_id,
                created,
                conv.message_count,
                first_msg
            );
        }

        println!();
        println!("{}", "═".repeat(80));
        println!("Total: {} conversation(s). Showing most recent first.", conversations.len());
        println!();
        println!("Examples:");
        println!("  openclaw claude --id <CONVERSATION_ID>  # View specific conversation");
        println!("  openclaw chat                           # Start a new conversation");
        println!("  openclaw chat --continue <ID>          # Continue existing conversation");

        Ok(())
    }

    /// Show a specific conversation with full message history
    fn show_conversation(
        openclaw: &OpenClaw,
        conversation_id: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let history = openclaw.get_conversation_history(conversation_id)?;

        if history.is_empty() {
            println!("No messages in this conversation.");
            return Ok(());
        }

        println!();
        println!("Conversation: {}", conversation_id);
        println!("Messages: {}", history.len());
        println!("{}", "═".repeat(80));

        // Display each message in the conversation
        for (i, msg) in history.iter().enumerate() {
            let role = if msg.role == "user" { "You" } else { "Claude" };
            println!();
            println!("[Message {}] {}:", i + 1, role);
            println!("{}", "─".repeat(40));
            // Handle multi-line content with proper indentation
            for line in msg.content.lines() {
                println!("{}", line);
            }
        }

        println!();
        println!("{}", "═".repeat(80));
        println!();
        println!("To continue this conversation:");
        println!("  openclaw chat --continue {}", conversation_id);

        Ok(())
    }
}
