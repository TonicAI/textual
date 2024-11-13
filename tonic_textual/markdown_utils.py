import re
from typing import List, Dict, Tuple, Union

MAX_HEADER_DEPTH = 6


def split_markdown(
    markdown: str, max_length: int
) -> List[Dict[str, Union[List[str], Tuple[int, int]]]]:
    return _split_by_header(markdown, max_length, 1, [], 0)


def _split_by_header(
    text: str,
    max_length: int,
    level: int,
    headers: List[str],
    base_index: int,
    max_header_depth: int = MAX_HEADER_DEPTH,
) -> List[Dict[str, Union[List[str], Tuple[int, int]]]]:
    header_pattern = re.compile(r"^(#{1," + str(level) + r"})\s+(.*)$", re.MULTILINE)
    sections = []
    last_index = 0

    for match in header_pattern.finditer(text):
        if match.start() > last_index:
            sections.append((last_index, match.start(), headers))
        headers = headers[: level - 1] + [match.group(2)]
        last_index = match.start()

    if last_index < len(text):
        sections.append((last_index, len(text), headers))

    split_sections = []
    for start, end, sec_headers in sections:
        section_length = end - start
        if section_length > max_length:
            if level < max_header_depth:
                split_sections.extend(
                    _split_by_header(
                        text[start:end],
                        max_length,
                        level + 1,
                        sec_headers,
                        base_index + start,
                    )
                )
            else:
                split_sections.extend(
                    _split_large_section(
                        text[start:end], max_length, sec_headers, base_index + start
                    )
                )
        else:
            split_sections.append(
                {
                    "headers": sec_headers,
                    "indices": (base_index + start, base_index + end),
                }
            )
    return split_sections


def _split_large_section(
    text: str, max_length: int, headers: List[str], base_index: int
) -> List[Dict[str, Union[List[str], Tuple[int, int]]]]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + max_length
        if end >= len(text):
            chunks.append(
                {
                    "headers": headers,
                    "indices": (base_index + start, base_index + len(text)),
                }
            )
            break

        newline_pos = text.rfind("\n", start, end)
        if newline_pos != -1 and newline_pos > start:
            chunks.append(
                {
                    "headers": headers,
                    "indices": (base_index + start, base_index + newline_pos),
                }
            )
            start = newline_pos + 1
        else:
            chunks.append(
                {"headers": headers, "indices": (base_index + start, base_index + end)}
            )
            start = end

    return chunks
