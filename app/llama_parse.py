import json
import mimetypes
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests


class ParsingMode(Enum):
    """The parsing mode to use."""

    PARSE_PAGE_WITHOUT_LLM = "parse_page_without_llm"
    PARSE_PAGE_WITH_LLM = "parse_page_with_llm"
    PARSE_PAGE_WITH_LVM = "parse_page_with_lvm"
    PARSE_PAGE_WITH_AGENT = "parse_page_with_agent"
    PARSE_PAGE_WITH_LAYOUT_AGENT = "parse_page_with_layout_agent"
    PARSE_DOCUMENT_WITH_LLM = "parse_document_with_llm"
    PARSE_DOCUMENT_WITH_AGENT = "parse_document_with_agent"


class AIModel(str, Enum):
    """The AI model to use. (depends on the parsing mode)"""

    OPENAI_GPT4O = "openai-gpt4o"
    OPENAI_GPT4O_MINI = "openai-gpt-4o-mini"
    OPENAI_GPT_4_1_NANO = "openai-gpt-4-1-nano"
    OPENAI_GPT_4_1_MINI = "openai-gpt-4-1-mini"
    OPENAI_GPT_4_1 = "openai-gpt-4-1"
    ANTHROPIC_SONNET_3_5 = "anthropic-sonnet-3.5"
    ANTHROPIC_SONNET_3_7 = "anthropic-sonnet-3.7"
    ANTHROPIC_SONNET_4_0 = "anthropic-sonnet-4.0"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"


class ResultType(Enum):
    """The type of result to return."""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"


@dataclass
class ParseConfig:
    """Configuration for parsing parameters"""

    parsing_mode: ParsingMode = ParsingMode.PARSE_DOCUMENT_WITH_LLM
    result_type: ResultType = ResultType.MARKDOWN
    use_vendor_multimodal_model: bool = False
    vendor_multimodal_model_name: Optional[str] = None
    vendor_multimodal_api_key: Optional[str] = None
    auto_mode: bool = True
    auto_mode_trigger_on_table_in_page: bool = True
    auto_mode_trigger_on_image_in_page: bool = True
    language: str = "en"
    disable_ocr: bool = False
    skip_diagonal_text: bool = False
    do_not_unroll_columns: bool = False
    target_pages: Optional[str] = None
    page_separator: str = "\n=================\n"
    page_prefix: str = "START OF PAGE: {pageNumber}\n"
    page_suffix: str = "\nEND OF PAGE: {pageNumber}"
    bounding_box: Optional[str] = None  # Legacy; use bbox_*
    bbox_top: Optional[float] = None
    bbox_bottom: Optional[float] = None
    bbox_left: Optional[float] = None
    bbox_right: Optional[float] = None
    take_screenshot: bool = False
    disable_image_extraction: bool = True
    spreadsheet_extract_sub_tables: bool = False
    output_tables_as_HTML: bool = False
    preserve_layout_alignment_across_pages: bool = False
    hide_headers: bool = False
    hide_footers: bool = False
    page_header_prefix: str = ""
    page_header_suffix: str = ""
    page_footer_prefix: str = ""
    page_footer_suffix: str = ""
    merge_tables_across_pages_in_markdown: bool = False
    invalidate_cache: bool = False
    do_not_cache: bool = False
    structured_output: bool = False
    structured_output_json_schema: Optional[str] = None
    job_timeout_in_seconds: Optional[int] = 120
    job_timeout_extra_time_per_page_in_seconds: Optional[int] = None
    strict_mode_image_extraction: bool = False
    strict_mode_image_ocr: bool = False
    strict_mode_reconstruction: bool = True
    strict_mode_buggy_fonts: bool = True
    max_pages: Optional[int] = None
    user_prompt: Optional[str] = None
    system_prompt_append: Optional[str] = None
    system_prompt: Optional[str] = None
    high_res_ocr: bool = False
    adaptive_long_table: bool = False
    annotate_links: bool = False
    html_make_all_elements_visible: bool = False
    html_remove_navigation_elements: bool = False
    html_remove_fixed_elements: bool = False
    guess_xlsx_sheet_name: bool = False
    output_pdf_of_document: bool = False


class LlamaParseRESTClient:
    """LlamaParse REST API client for extracting data from files."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LlamaCloud API key must be provided or set as LLAMA_CLOUD_API_KEY environment variable"
            )

        self.base_url = "https://api.cloud.llamaindex.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
        }

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for the file."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type

        extension_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".html": "text/html",
            ".txt": "text/plain",
            ".jpeg": "image/jpeg",
            ".jpg": "image/jpeg",
            ".png": "image/png",
        }

        return extension_map.get(file_path.suffix.lower(), "application/octet-stream")

    def _build_form_data(self, config: ParseConfig) -> Dict[str, Any]:
        """Build form data for the upload request."""
        form_data = {}

        form_data["parsing_mode"] = config.parsing_mode.value

        # AI model selection (only for certain parsing modes)
        model_supported_modes = {
            ParsingMode.PARSE_PAGE_WITH_LVM,
            ParsingMode.PARSE_PAGE_WITH_AGENT,
            ParsingMode.PARSE_DOCUMENT_WITH_LLM,
            ParsingMode.PARSE_DOCUMENT_WITH_AGENT,
        }

        if config.parsing_mode in model_supported_modes:
            if (
                config.use_vendor_multimodal_model
                and config.vendor_multimodal_model_name
            ):
                form_data["vendor_multimodal_model"] = (
                    config.vendor_multimodal_model_name
                )
                if config.vendor_multimodal_api_key:
                    form_data["vendor_multimodal_api_key"] = (
                        config.vendor_multimodal_api_key
                    )

        if config.result_type != ResultType.MARKDOWN:
            form_data["result_type"] = config.result_type.value

        if config.auto_mode:
            form_data["auto_mode"] = "true"
            form_data["auto_mode_trigger_on_image_in_page"] = str(
                config.auto_mode_trigger_on_image_in_page
            ).lower()
            form_data["auto_mode_trigger_on_table_in_page"] = str(
                config.auto_mode_trigger_on_table_in_page
            ).lower()

        if config.language != "en":
            form_data["language"] = config.language

        form_data["disable_ocr"] = str(config.disable_ocr).lower()
        form_data["skip_diagonal_text"] = str(config.skip_diagonal_text).lower()
        form_data["do_not_unroll_columns"] = str(config.do_not_unroll_columns).lower()

        if config.target_pages:
            form_data["target_pages"] = config.target_pages

        if config.max_pages:
            form_data["max_pages"] = str(config.max_pages)

        form_data["page_separator"] = config.page_separator
        form_data["page_prefix"] = config.page_prefix
        form_data["page_suffix"] = config.page_suffix

        # Bounding box (both legacy and new format support)
        if config.bounding_box:
            form_data["bounding_box"] = config.bounding_box
        else:
            bbox_parts = []
            if config.bbox_top is not None:
                bbox_parts.append(f"top:{config.bbox_top}")
            if config.bbox_bottom is not None:
                bbox_parts.append(f"bottom:{config.bbox_bottom}")
            if config.bbox_left is not None:
                bbox_parts.append(f"left:{config.bbox_left}")
            if config.bbox_right is not None:
                bbox_parts.append(f"right:{config.bbox_right}")
            if bbox_parts:
                form_data["bounding_box"] = ",".join(bbox_parts)

        form_data["take_screenshot"] = str(config.take_screenshot).lower()
        form_data["disable_image_extraction"] = str(
            config.disable_image_extraction
        ).lower()
        form_data["strict_mode_image_extraction"] = str(
            config.strict_mode_image_extraction
        ).lower()
        form_data["strict_mode_image_ocr"] = str(config.strict_mode_image_ocr).lower()

        form_data["spreadsheet_extract_sub_tables"] = str(
            config.spreadsheet_extract_sub_tables
        ).lower()
        form_data["output_tables_as_HTML"] = str(config.output_tables_as_HTML).lower()
        form_data["merge_tables_across_pages_in_markdown"] = str(
            config.merge_tables_across_pages_in_markdown
        ).lower()
        form_data["adaptive_long_table"] = str(config.adaptive_long_table).lower()

        form_data["preserve_layout_alignment_across_pages"] = str(
            config.preserve_layout_alignment_across_pages
        ).lower()
        form_data["hide_headers"] = str(config.hide_headers).lower()
        form_data["hide_footers"] = str(config.hide_footers).lower()

        if config.page_header_prefix:
            form_data["page_header_prefix"] = config.page_header_prefix
        if config.page_header_suffix:
            form_data["page_header_suffix"] = config.page_header_suffix
        if config.page_footer_prefix:
            form_data["page_footer_prefix"] = config.page_footer_prefix
        if config.page_footer_suffix:
            form_data["page_footer_suffix"] = config.page_footer_suffix

        form_data["invalidate_cache"] = str(config.invalidate_cache).lower()
        form_data["do_not_cache"] = str(config.do_not_cache).lower()

        form_data["structured_output"] = str(config.structured_output).lower()
        if config.structured_output_json_schema:
            form_data["structured_output_json_schema"] = (
                config.structured_output_json_schema
            )

        if config.job_timeout_in_seconds:
            form_data["job_timeout_in_seconds"] = str(config.job_timeout_in_seconds)
        if config.job_timeout_extra_time_per_page_in_seconds:
            form_data["job_timeout_extra_time_per_page_in_seconds"] = str(
                config.job_timeout_extra_time_per_page_in_seconds
            )

        form_data["strict_mode_reconstruction"] = str(
            config.strict_mode_reconstruction
        ).lower()
        form_data["strict_mode_buggy_fonts"] = str(
            config.strict_mode_buggy_fonts
        ).lower()

        if config.user_prompt:
            form_data["user_prompt"] = config.user_prompt
        if config.system_prompt:
            form_data["system_prompt"] = config.system_prompt
        if config.system_prompt_append:
            form_data["system_prompt_append"] = config.system_prompt_append

        form_data["high_res_ocr"] = str(config.high_res_ocr).lower()
        form_data["annotate_links"] = str(config.annotate_links).lower()
        form_data["guess_xlsx_sheet_name"] = str(config.guess_xlsx_sheet_name).lower()
        form_data["output_pdf_of_document"] = str(config.output_pdf_of_document).lower()

        form_data["html_make_all_elements_visible"] = str(
            config.html_make_all_elements_visible
        ).lower()
        form_data["html_remove_navigation_elements"] = str(
            config.html_remove_navigation_elements
        ).lower()
        form_data["html_remove_fixed_elements"] = str(
            config.html_remove_fixed_elements
        ).lower()

        return form_data

    def upload_and_parse(
        self, file_path: Union[str, Path], config: Optional[ParseConfig] = None
    ) -> str:
        """Upload a file and start parsing."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        supported_extensions = {
            ".pdf",
            ".docx",
            ".doc",
            ".pptx",
            ".xlsx",
            ".html",
            ".txt",
            ".jpeg",
            ".jpg",
            ".png",
        }
        if file_path.suffix.lower() not in supported_extensions:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        config = config or ParseConfig()
        mime_type = self._get_mime_type(file_path)

        with open(file_path, "rb") as file:
            files = {"file": (file_path.name, file, mime_type)}

            data = self._build_form_data(config)

            response = requests.post(
                f"{self.base_url}/parsing/upload",
                headers=self.headers,
                files=files,
                data=data,
            )

        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")

        result = response.json()
        return result.get("id") or result.get("job_id")

    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a parsing job."""
        response = requests.get(
            f"{self.base_url}/parsing/job/{job_id}", headers=self.headers
        )

        if response.status_code != 200:
            raise Exception(
                f"Status check failed: {response.status_code} - {response.text}"
            )

        return response.json()

    def get_result_markdown(self, job_id: str) -> str:
        """Get parsing results in Markdown format."""
        response = requests.get(
            f"{self.base_url}/parsing/job/{job_id}/result/markdown",
            headers=self.headers,
        )

        if response.status_code != 200:
            raise Exception(
                f"Result retrieval failed: {response.status_code} - {response.text}"
            )

        result = response.json()
        return result.get("markdown", "")

    def get_result_text(self, job_id: str) -> str:
        """Get parsing results in text format."""
        response = requests.get(
            f"{self.base_url}/parsing/job/{job_id}/result/text", headers=self.headers
        )

        if response.status_code != 200:
            raise Exception(
                f"Result retrieval failed: {response.status_code} - {response.text}"
            )

        result = response.json()
        return result.get("text", "")

    def get_result_json(self, job_id: str) -> Dict[str, Any]:
        """Get parsing results in JSON format."""
        response = requests.get(
            f"{self.base_url}/parsing/job/{job_id}/result/json", headers=self.headers
        )

        if response.status_code != 200:
            raise Exception(
                f"Result retrieval failed: {response.status_code} - {response.text}"
            )

        return response.json()

    def wait_for_completion(
        self, job_id: str, max_wait_time: int = 300, poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Wait for a parsing job to complete."""
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status = self.check_job_status(job_id)

            if status.get("status") == "SUCCESS":
                return status
            elif status.get("status") == "ERROR":
                raise Exception(
                    f"Parsing failed: {status.get('error', 'Unknown error')}"
                )

            time.sleep(poll_interval)

        raise TimeoutError(
            f"Job {job_id} did not complete within {max_wait_time} seconds"
        )

    def extract_from_file(
        self,
        file_path: Union[str, Path],
        config: Optional[ParseConfig] = None,
        wait_for_completion: bool = True,
        max_wait_time: int = 300,
    ) -> Dict[str, Any]:
        """Complete extraction workflow: upload, parse, and retrieve results."""
        file_path = Path(file_path)
        config = config or ParseConfig()

        try:
            # Upload and start parsing
            job_id = self.upload_and_parse(file_path, config)

            result = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "file_type": file_path.suffix.lower(),
                "job_id": job_id,
                "config": {
                    "result_type": config.result_type.value,
                    "parsing_mode": config.parsing_mode.value,
                    "language": config.language,
                    "user_prompt": config.user_prompt,
                    "target_pages": config.target_pages,
                    "bounding_box": config.bounding_box,
                },
                "success": False,
                "status": "PENDING",
                "content": None,
                "metadata": {},
                "error": None,
            }

            if not wait_for_completion:
                return result

            # Wait for completion
            final_status = self.wait_for_completion(job_id, max_wait_time)
            result["status"] = final_status.get("status")

            if config.result_type == ResultType.MARKDOWN:
                content = self.get_result_markdown(job_id)
            elif config.result_type == ResultType.TEXT:
                content = self.get_result_text(job_id)
            elif config.result_type == ResultType.JSON:
                content = self.get_result_json(job_id)
            else:
                content = self.get_result_markdown(job_id)

            result["content"] = content
            result["success"] = True

            if isinstance(content, str):
                result["metadata"] = {
                    "total_characters": len(content),
                    "total_words": len(content.split()),
                    "processing_time": final_status.get("processing_time"),
                    "pages_processed": final_status.get("pages_processed"),
                }
            elif isinstance(content, dict):
                result["metadata"] = {
                    "json_keys": list(content.keys()) if content else [],
                    "processing_time": final_status.get("processing_time"),
                    "pages_processed": final_status.get("pages_processed"),
                }

            return result

        except Exception as e:
            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "success": False,
                "status": "ERROR",
                "error": str(e),
                "content": None,
                "metadata": {},
            }

    def extract_from_multiple_files(
        self,
        file_paths: List[Union[str, Path]],
        config: Optional[ParseConfig] = None,
        max_concurrent: int = 5,
        max_wait_time: int = 300,
    ) -> List[Dict[str, Any]]:
        """Extract data from multiple files."""
        config = config or ParseConfig()
        results = []
        active_jobs = []

        for i, file_path in enumerate(file_paths):
            try:
                job_id = self.upload_and_parse(file_path, config)
                active_jobs.append(
                    {"job_id": job_id, "file_path": Path(file_path), "index": i}
                )

                # Process in batches
                if len(active_jobs) >= max_concurrent or i == len(file_paths) - 1:
                    batch_results = self._process_job_batch(
                        active_jobs, config, max_wait_time
                    )
                    results.extend(batch_results)
                    active_jobs = []

            except Exception as e:
                results.append(
                    {
                        "file_path": str(file_path),
                        "file_name": Path(file_path).name,
                        "success": False,
                        "error": str(e),
                        "content": None,
                        "metadata": {},
                    }
                )

        return results

    def _process_job_batch(
        self, jobs: List[Dict[str, Any]], config: ParseConfig, max_wait_time: int
    ) -> List[Dict[str, Any]]:
        """Process a batch of jobs."""
        results = []

        for job_info in jobs:
            try:
                final_status = self.wait_for_completion(
                    job_info["job_id"], max_wait_time
                )

                if config.result_type == ResultType.MARKDOWN:
                    content = self.get_result_markdown(job_info["job_id"])
                elif config.result_type == ResultType.TEXT:
                    content = self.get_result_text(job_info["job_id"])
                elif config.result_type == ResultType.JSON:
                    content = self.get_result_json(job_info["job_id"])
                else:
                    content = self.get_result_markdown(job_info["job_id"])

                file_path = job_info["file_path"]
                result = {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "file_type": file_path.suffix.lower(),
                    "job_id": job_info["job_id"],
                    "success": True,
                    "status": final_status.get("status"),
                    "content": content,
                    "metadata": {
                        "processing_time": final_status.get("processing_time"),
                        "pages_processed": final_status.get("pages_processed"),
                    },
                }

                if isinstance(content, str):
                    result["metadata"].update(
                        {
                            "total_characters": len(content),
                            "total_words": len(content.split()),
                        }
                    )

                results.append(result)

            except Exception as e:
                file_path = job_info["file_path"]
                results.append(
                    {
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "success": False,
                        "error": str(e),
                        "content": None,
                        "metadata": {},
                    }
                )

        return results

    def save_results(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]],
        output_dir: Union[str, Path],
        format_type: str = "original",
    ) -> None:
        """Save extraction results to files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(results, dict):
            results = [results]

        for result in results:
            if not result.get("success", False):
                continue

            file_name = Path(result["file_name"]).stem
            content = result.get("content", "")

            if format_type == "json" or (
                format_type == "original" and isinstance(content, dict)
            ):
                output_file = output_dir / f"{file_name}_extracted.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    if isinstance(content, dict):
                        json.dump(content, f, indent=2, ensure_ascii=False)
                    else:
                        json.dump(result, f, indent=2, ensure_ascii=False)

            elif format_type == "markdown" or (
                format_type == "original"
                and result["config"]["result_type"] == "markdown"
            ):
                output_file = output_dir / f"{file_name}_extracted.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    if isinstance(content, str):
                        f.write(content)
                    else:
                        f.write(f"# Extracted from: {result['file_name']}\n\n")
                        f.write(str(content))

            else:  # text format
                output_file = output_dir / f"{file_name}_extracted.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    if isinstance(content, str):
                        f.write(content)
                    else:
                        f.write(f"Extracted from: {result['file_name']}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(str(content))