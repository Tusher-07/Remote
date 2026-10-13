from app.ui import build_ui


def main() -> None:
    
    """Entry point script for launching the application."""
    demo = build_ui()
    demo.launch(share=True)

if __name__ == "__main__":
    main()
