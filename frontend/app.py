#!/usr/bin/env python3
"""
TukuyBooks Streamlit Frontend

This application provides a web interface for the TukuyBooks Ebook Maker.
It allows users to:
- Run spiders to gather documentation
- Convert the scraped data to EPUB format
- Convert EPUBs to PDF
- View available documentation spiders

The application is built using Streamlit and interfaces with the
backend script 'tukuy_ebook_maker.py'
"""

import os
import sys
import time
import subprocess
import streamlit as st
import pandas as pd

# Add the backend scripts directory to path so we can import from there
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "backend", "scripts")
sys.path.insert(0, BACKEND_SCRIPTS_DIR)


# Import modules from file paths dynamically
def import_module_from_path(module_name, file_path):
    """Import a module from a file path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(
            f"Could not find module {module_name} at {file_path}"
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Import the backend modules
try:
    # Import using file paths
    tukuy_ebook_maker_path = os.path.join(
        BACKEND_SCRIPTS_DIR, "tukuy_ebook_maker.py"
    )
    spider_runner_path = os.path.join(BACKEND_SCRIPTS_DIR, "spider_runner.py")

    if not os.path.exists(tukuy_ebook_maker_path):
        raise ImportError(
            f"Could not find tukuy_ebook_maker.py at {tukuy_ebook_maker_path}"
        )
    if not os.path.exists(spider_runner_path):
        raise ImportError(
            f"Could not find spider_runner.py at {spider_runner_path}"
        )

    tukuy_ebook_maker = import_module_from_path(
        "tukuy_ebook_maker", tukuy_ebook_maker_path
    )
    spider_runner = import_module_from_path(
        "spider_runner", spider_runner_path
    )

except ImportError as e:
    st.error(f"Failed to import backend modules: {e}")
    st.error(f"Current Python path: {sys.path}")
    st.error(f"Looking for modules in: {BACKEND_SCRIPTS_DIR}")
    st.stop()

# Set page configuration
st.set_page_config(
    page_title="TukuyBooks Ebook Maker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1e7dd;
        border: 1px solid #badbcc;
        color: #0f5132;
        margin-bottom: 1rem;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c2c7;
        color: #842029;
        margin-bottom: 1rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #cfe2ff;
        border: 1px solid #b6d4fe;
        color: #084298;
        margin-bottom: 1rem;
    }
    .output-area {
        background-color: #f8f9fa;
        border-radius: 0.25rem;
        padding: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Helper functions
def get_available_spiders():
    """Get a list of available spiders from config.json"""
    config = tukuy_ebook_maker.load_spider_config()
    spiders = config.get("spiders", {})

    result = []
    if isinstance(spiders, dict):
        for spider_id, spider_info in spiders.items():
            result.append(
                {
                    "id": spider_id,
                    "description": spider_info.get("description", ""),
                }
            )
    elif isinstance(spiders, list):
        for spider in spiders:
            if isinstance(spider, dict):
                result.append(
                    {
                        "id": spider.get("id", "unknown"),
                        "description": spider.get("description", ""),
                    }
                )
            else:
                result.append({"id": str(spider), "description": ""})

    return result


def get_available_epub_files():
    """Get a list of available EPUB files in outputs directory"""
    outputs_dir = os.path.join(PROJECT_ROOT, "backend", "outputs")
    epub_files = []

    if os.path.isdir(outputs_dir):
        for file in os.listdir(outputs_dir):
            if file.endswith(".epub"):
                file_path = os.path.join(outputs_dir, file)
                file_size = os.path.getsize(file_path)
                modified_time = os.path.getmtime(file_path)

                epub_files.append(
                    {
                        "name": file,
                        "path": file_path,
                        "size": file_size,
                        "modified": modified_time,
                    }
                )

    return sorted(epub_files, key=lambda x: x["modified"], reverse=True)


def get_available_pdf_files():
    """Get a list of available PDF files in outputs/converted directory"""
    outputs_dir = os.path.join(PROJECT_ROOT, "backend", "outputs", "converted")
    pdf_files = []

    if os.path.isdir(outputs_dir):
        for file in os.listdir(outputs_dir):
            if file.endswith(".pdf"):
                file_path = os.path.join(outputs_dir, file)
                file_size = os.path.getsize(file_path)
                modified_time = os.path.getmtime(file_path)

                pdf_files.append(
                    {
                        "name": file,
                        "path": file_path,
                        "size": file_size,
                        "modified": modified_time,
                    }
                )

    return sorted(pdf_files, key=lambda x: x["modified"], reverse=True)


def run_spider_with_progress(spider_id):
    """Run a spider with progress updates"""
    progress_text = st.empty()
    progress_bar = st.progress(0.0)
    output_area = st.empty()

    # Create a list to capture output
    output = []

    # Set up console redirect
    import io
    import contextlib
    from threading import Thread
    import time

    # Create a StringIO object to capture stdout
    stdout_capture = io.StringIO()

    # Function to periodically check for new output
    def update_ui_from_capture():
        last_pos = 0
        stages = {
            "Starting crawl": 0.1,
            "Crawling page": 0.3,
            "Processing items": 0.7,
            "Finished crawl": 0.95,
        }

        while True:
            # Get any new output
            stdout_capture.seek(last_pos)
            new_output = stdout_capture.read()

            if new_output:
                lines = new_output.splitlines()
                for line in lines:
                    if line.strip():
                        output.append(line.strip())

                        # Update progress based on keywords
                        for keyword, value in stages.items():
                            if keyword in line:
                                progress_bar.progress(value)
                                break

                # Update the UI
                progress_text.write(
                    f"Progress: {output[-1] if output else 'Starting...'}"
                )
                output_area.code("\n".join(output[-20:]))  # Show last 20 lines

                # Update position
                last_pos = stdout_capture.tell()

            # Check if the thread should exit
            if (
                hasattr(update_ui_from_capture, "stop")
                and update_ui_from_capture.stop
            ):
                break

            time.sleep(0.1)

    # Start the UI update thread
    update_thread = Thread(target=update_ui_from_capture)
    update_thread.daemon = True
    update_thread.start()

    try:
        progress_text.write("Starting spider...")
        progress_bar.progress(0.05)

        # Redirect stdout to our capture
        with contextlib.redirect_stdout(stdout_capture):
            success = spider_runner.run_spider(spider_id)

        if success:
            progress_bar.progress(1.0)
            progress_text.write("Spider completed successfully!")
        else:
            progress_text.write("Spider failed or not found.")

        # Stop the UI update thread
        update_ui_from_capture.stop = True
        update_thread.join(timeout=1.0)

        return success, "\n".join(output)
    except Exception as e:
        # Stop the UI update thread
        if "update_ui_from_capture" in locals():
            update_ui_from_capture.stop = True
            update_thread.join(timeout=1.0)

        progress_text.write(f"Error running spider: {str(e)}")
        return False, str(e)


def create_ebook_with_progress(spider_id, output_filename=None):
    """Create an ebook with progress updates"""
    progress_text = st.empty()
    progress_bar = st.progress(0.0)
    output_area = st.empty()

    # Create a list to capture output
    output = []

    # Set up console redirect
    import io
    import contextlib
    from threading import Thread
    import time

    # Create a StringIO object to capture stdout
    stdout_capture = io.StringIO()

    # Function to periodically check for new output
    def update_ui_from_capture():
        last_pos = 0

        while True:
            # Get any new output
            stdout_capture.seek(last_pos)
            new_output = stdout_capture.read()

            if new_output:
                lines = new_output.splitlines()
                for line in lines:
                    if line.strip():
                        output.append(line.strip())

                # Update the UI
                if output:
                    output_area.code(
                        "\n".join(output[-20:])
                    )  # Show last 20 lines

                # Update position
                last_pos = stdout_capture.tell()

            # Check if the thread should exit
            if (
                hasattr(update_ui_from_capture, "stop")
                and update_ui_from_capture.stop
            ):
                break

            time.sleep(0.1)

    # Start the UI update thread
    update_thread = Thread(target=update_ui_from_capture)
    update_thread.daemon = True
    update_thread.start()

    try:
        progress_text.write("Initializing ebook creation...")
        progress_bar.progress(0.1)

        # Select the correct EbookMaker class
        if spider_id == "python_docs":
            maker = tukuy_ebook_maker.PythonDocsEbookMaker()
        elif spider_id == "mdn_docs":
            maker = tukuy_ebook_maker.MDNEbookMaker()
        elif spider_id == "react_docs":
            maker = tukuy_ebook_maker.ReactEbookMaker()
        else:
            progress_text.write(f"Unknown spider ID: {spider_id}")
            return False, f"Unknown spider ID: {spider_id}"

        # Show loading chapters
        progress_text.write("Loading chapters...")
        progress_bar.progress(0.2)

        # Override the create_epub method to provide progress updates
        original_create_epub = maker.create_epub

        def create_epub_with_progress(output_filename=None):
            # Call original method but update progress
            progress_text.write("Processing chapters...")
            progress_bar.progress(0.4)

            # Use our stdout capture
            with contextlib.redirect_stdout(stdout_capture):
                result = original_create_epub(output_filename)

            if result:
                progress_text.write(f"EPUB created: {result}")
                progress_bar.progress(1.0)
            else:
                progress_text.write("Failed to create EPUB")

            return result

        maker.create_epub = create_epub_with_progress

        # Create the ebook
        result = maker.create_epub(output_filename)

        # Stop the UI update thread
        update_ui_from_capture.stop = True
        update_thread.join(timeout=1.0)

        if result:
            return True, result
        else:
            return False, "\n".join(output) or "Failed to create EPUB"
    except Exception as e:
        import traceback

        # Stop the UI update thread if it exists
        if "update_ui_from_capture" in locals():
            update_ui_from_capture.stop = True
            update_thread.join(timeout=1.0)

        progress_text.write(f"Error creating ebook: {str(e)}")
        return False, traceback.format_exc()


def convert_epub_to_pdf(epub_filename):
    """Convert an EPUB file to PDF using book_converter.sh"""
    progress_text = st.empty()
    progress_bar = st.progress(0.0)
    output_area = st.empty()

    try:
        converter_script = os.path.join(
            BACKEND_SCRIPTS_DIR, "book_converter.sh"
        )

        if not os.path.isfile(converter_script):
            progress_text.write(
                f"Converter script not found: {converter_script}"
            )
            return False, f"Converter script not found: {converter_script}"

        # Set environment variables
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["INPUT_EPUB"] = epub_filename

        progress_text.write(
            f"Converting {os.path.basename(epub_filename)} to PDF..."
        )
        progress_bar.progress(0.1)

        # Start the conversion process
        process = subprocess.Popen(
            ["bash", converter_script],
            cwd=BACKEND_SCRIPTS_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        output = []
        # Read the output incrementally
        for line in iter(process.stdout.readline, ""):
            output.append(line.strip())
            output_area.code("\n".join(output[-20:]))  # Show last 20 lines

            # Update progress based on certain output markers
            if "Starting conversion" in line:
                progress_bar.progress(0.2)
            elif "Converting EPUB to PDF" in line:
                progress_bar.progress(0.5)
            elif "Conversion completed" in line:
                progress_bar.progress(0.9)

        process.wait()

        if process.returncode == 0:
            progress_bar.progress(1.0)
            progress_text.write("Conversion completed successfully!")
            return True, "\n".join(output)
        else:
            progress_text.write("Conversion failed.")
            return False, "\n".join(output)
    except Exception as e:
        import traceback

        progress_text.write(f"Error during conversion: {str(e)}")
        return False, traceback.format_exc()


def format_size(size_bytes):
    """Format file size from bytes to appropriate unit"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def display_files_table(files, file_type="EPUB"):
    """Display a table of files with download buttons"""
    if not files:
        st.info(f"No {file_type} files available.")
        return

    # Create a dataframe for display
    df_data = []
    for file in files:
        df_data.append(
            {
                "Name": file["name"],
                "Size": format_size(file["size"]),
                "Modified": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(file["modified"])
                ),
            }
        )

    df = pd.DataFrame(df_data)

    # Display the table
    st.dataframe(df, use_container_width=True)

    # Add download buttons
    col1, col2 = st.columns(2)
    with col1:
        selected_file = st.selectbox(
            f"Select {file_type} file to download",
            options=[file["name"] for file in files],
            key=f"select_{file_type.lower()}",
        )

    with col2:
        file_path = next(
            (file["path"] for file in files if file["name"] == selected_file),
            None,
        )
        if file_path:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            st.download_button(
                label=f"Download {selected_file}",
                data=file_bytes,
                file_name=selected_file,
                mime=f"application/{file_type.lower()}",
                key=f"download_{file_type.lower()}",
            )


# Main application
def main():
    st.title("📚 TukuyBooks Ebook Maker")
    st.markdown("""
    This application provides a web interface for the TukuyBooks Ebook Maker.
    It allows you to run documentation spiders, create ebooks, and convert them to PDF format.
    """)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Run Spider", "Create Ebook", "Convert to PDF", "View Files"],
    )

    if page == "Home":
        st.header("Welcome to TukuyBooks Ebook Maker")
        st.markdown("""
        TukuyBooks is a tool for creating documentation ebooks from various online sources.
        
        ### Available Features:
        
        1. **Run Spider**: Crawl documentation websites and extract content
        2. **Create Ebook**: Convert scraped data into EPUB format
        3. **Convert to PDF**: Convert EPUB files to PDF format
        4. **View Files**: Browse and download created ebooks
        
        ### Available Documentation Sources:
        """)

        # Display available spiders
        spiders = get_available_spiders()
        if spiders:
            spider_data = []
            for spider in spiders:
                spider_data.append(
                    {
                        "Spider ID": spider["id"],
                        "Description": spider["description"],
                    }
                )
            st.table(pd.DataFrame(spider_data))
        else:
            st.info("No documentation spiders configured.")

    elif page == "Run Spider":
        st.header("Run Documentation Spider")
        st.markdown(
            "Select a spider to run and extract documentation content."
        )

        # Get available spiders
        spiders = get_available_spiders()
        if not spiders:
            st.error("No documentation spiders configured.")
            return

        # Create selection box
        spider_options = {
            spider["id"]: spider["description"] for spider in spiders
        }
        selected_spider = st.selectbox(
            "Select spider to run",
            options=list(spider_options.keys()),
            format_func=lambda x: f"{x} - {spider_options[x]}"
            if spider_options[x]
            else x,
        )

        # Run button
        if st.button("Run Spider", type="primary"):
            with st.spinner(f"Running {selected_spider} spider..."):
                success, output = run_spider_with_progress(selected_spider)

                if success:
                    st.success(
                        f"Spider '{selected_spider}' completed successfully!"
                    )
                    # Show the output in a collapsible section
                    with st.expander("View Output"):
                        st.code(output)
                else:
                    st.error(f"Spider '{selected_spider}' failed.")
                    with st.expander("View Error Details"):
                        st.code(output)

    elif page == "Create Ebook":
        st.header("Create Ebook from Scraped Data")
        st.markdown("Convert spider output to EPUB format.")

        # Get available spiders
        spiders = get_available_spiders()
        if not spiders:
            st.error("No documentation spiders configured.")
            return

        # Create selection box for spider
        spider_options = {
            spider["id"]: spider["description"] for spider in spiders
        }
        selected_spider = st.selectbox(
            "Select spider data to convert",
            options=list(spider_options.keys()),
            format_func=lambda x: f"{x} - {spider_options[x]}"
            if spider_options[x]
            else x,
        )

        # Output filename
        custom_filename = st.text_input(
            "Output filename (optional, without extension)", ""
        )

        # Create button
        if st.button("Create Ebook", type="primary"):
            output_filename = (
                f"{custom_filename}.epub" if custom_filename else None
            )

            with st.spinner(f"Creating ebook from {selected_spider} data..."):
                success, result = create_ebook_with_progress(
                    selected_spider, output_filename
                )

                if success:
                    st.success(
                        f"Ebook created successfully: {os.path.basename(result)}"
                    )

                    # Offer download
                    with open(result, "rb") as f:
                        st.download_button(
                            label=f"Download {os.path.basename(result)}",
                            data=f.read(),
                            file_name=os.path.basename(result),
                            mime="application/epub+zip",
                        )
                else:
                    st.error("Failed to create ebook.")
                    with st.expander("View Error Details"):
                        st.code(result)

    elif page == "Convert to PDF":
        st.header("Convert EPUB to PDF")
        st.markdown(
            "Convert EPUB files to PDF format using book_converter.sh."
        )

        # Get available EPUB files
        epub_files = get_available_epub_files()
        if not epub_files:
            st.error("No EPUB files available to convert.")
            return

        # Create selection box for EPUB file
        selected_epub = st.selectbox(
            "Select EPUB file to convert",
            options=[file["name"] for file in epub_files],
        )

        epub_path = next(
            (
                file["path"]
                for file in epub_files
                if file["name"] == selected_epub
            ),
            None,
        )

        # Convert button
        if st.button("Convert to PDF", type="primary"):
            if not epub_path:
                st.error("Selected EPUB file not found.")
                return

            with st.spinner(f"Converting {selected_epub} to PDF..."):
                success, output = convert_epub_to_pdf(epub_path)

                if success:
                    st.success(
                        f"Converted {selected_epub} to PDF successfully!"
                    )

                    # Try to find the PDF file
                    pdf_name = selected_epub.replace(".epub", ".pdf")
                    pdf_path = os.path.join(
                        PROJECT_ROOT,
                        "backend",
                        "outputs",
                        "converted",
                        pdf_name,
                    )

                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label=f"Download {pdf_name}",
                                data=f.read(),
                                file_name=pdf_name,
                                mime="application/pdf",
                            )
                else:
                    st.error("Conversion failed.")
                    with st.expander("View Error Details"):
                        st.code(output)

    elif page == "View Files":
        st.header("View Generated Files")

        tab1, tab2 = st.tabs(["EPUB Files", "PDF Files"])

        with tab1:
            st.subheader("Available EPUB Files")
            epub_files = get_available_epub_files()
            display_files_table(epub_files, "EPUB")

        with tab2:
            st.subheader("Available PDF Files")
            pdf_files = get_available_pdf_files()
            display_files_table(pdf_files, "PDF")


if __name__ == "__main__":
    main()
