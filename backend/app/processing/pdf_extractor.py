from pathlib import Path

import fitz


def clean_text(text: str) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n".join(lines)


def extract_pdf_pages(
    file_path: str,
) -> list[dict]:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            "PDF file does not exist."
        )

    pages: list[dict] = []

    pdf = fitz.open(path)

    try:
        for page_index in range(
            pdf.page_count
        ):
            page = pdf.load_page(
                page_index
            )

            text = page.get_text("text")

            cleaned_text = clean_text(
                text
            )

            if not cleaned_text:
                continue

            pages.append(
                {
                    "page_number":
                        page_index + 1,
                    "text":
                        cleaned_text,
                }
            )

    finally:
        pdf.close()

    return pages