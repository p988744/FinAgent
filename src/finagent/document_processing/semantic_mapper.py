"""Semantic concept mapping for documents."""

import sqlite3


def lookup_concepts_by_synonym(
    synonym: str, db_path: str = "data/finagent.db", threshold: float = 0.5
) -> list[tuple[str, float]]:
    """
    Look up concept keys matching a synonym.

    Args:
        synonym: Term to search for (e.g., "洗錢", "創投公司")
        db_path: Path to database
        threshold: Minimum weight threshold (0-1)

    Returns:
        List of (concept_key, weight) tuples sorted by weight descending
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Try exact match first
    cursor.execute(
        """
        SELECT DISTINCT concept_key, weight
        FROM concept_synonyms
        WHERE synonym = ?
        AND weight >= ?
        ORDER BY weight DESC
    """,
        (synonym, threshold),
    )
    results = cursor.fetchall()

    # If no exact match, try FTS fuzzy search (escape special characters)
    if not results:
        try:
            # Quote the search term for FTS to handle special characters
            fts_query = f'"{synonym}"'
            cursor.execute(
                """
                SELECT DISTINCT cs.concept_key, cs.weight
                FROM concept_synonyms_fts fts
                JOIN concept_synonyms cs ON fts.rowid = cs.id
                WHERE fts.synonym MATCH ?
                AND cs.weight >= ?
                ORDER BY cs.weight DESC
                LIMIT 5
            """,
                (fts_query, threshold),
            )
            results = cursor.fetchall()
        except sqlite3.OperationalError:
            # FTS query failed, skip to partial match
            results = []

    # If still no match, try partial match (LIKE)
    if not results:
        cursor.execute(
            """
            SELECT DISTINCT concept_key, weight
            FROM concept_synonyms
            WHERE synonym LIKE ?
            AND weight >= ?
            ORDER BY weight DESC
            LIMIT 5
        """,
            (f"%{synonym}%", threshold),
        )
        results = cursor.fetchall()

    conn.close()
    return results


def get_all_concept_synonyms(concept_key: str, db_path: str = "data/finagent.db") -> list[str]:
    """
    Get all synonyms for a given concept.

    Args:
        concept_key: Concept key (e.g., "ANTI_MONEY_LAUNDERING")
        db_path: Path to database

    Returns:
        List of synonyms
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT synonym
        FROM concept_synonyms
        WHERE concept_key = ?
        ORDER BY weight DESC
    """,
        (concept_key,),
    )
    synonyms = [row[0] for row in cursor.fetchall()]
    conn.close()
    return synonyms


def assign_concepts_to_document(
    filename: str,
    violation_types: list[str] = None,
    related_institutions: list[str] = None,
    issuing_authority: str = None,
    keywords: list[str] = None,
    db_path: str = "data/finagent.db",
) -> list[tuple[str, float]]:
    """
    Map document metadata to semantic concepts and store in database.

    Args:
        filename: Document filename
        violation_types: List of violation types from metadata
        related_institutions: List of related institutions
        issuing_authority: Issuing authority
        keywords: List of keywords
        db_path: Path to database

    Returns:
        List of (concept_key, confidence) tuples that were assigned
    """
    concepts_to_assign = {}  # {concept_key: confidence}

    # 1. Map violation_types to concepts
    if violation_types:
        for violation in violation_types:
            matches = lookup_concepts_by_synonym(violation, db_path, threshold=0.6)
            for concept_key, weight in matches:
                # Use max confidence if concept already found
                concepts_to_assign[concept_key] = max(
                    concepts_to_assign.get(concept_key, 0.0), weight
                )

    # 2. Map related_institutions to concepts
    if related_institutions:
        for institution in related_institutions:
            matches = lookup_concepts_by_synonym(institution, db_path, threshold=0.6)
            for concept_key, weight in matches:
                concepts_to_assign[concept_key] = max(
                    concepts_to_assign.get(concept_key, 0.0), weight
                )

    # 3. Map issuing_authority to concepts
    if issuing_authority:
        matches = lookup_concepts_by_synonym(issuing_authority, db_path, threshold=0.6)
        for concept_key, weight in matches:
            concepts_to_assign[concept_key] = max(concepts_to_assign.get(concept_key, 0.0), weight)

    # 4. Map keywords (top 5 only to avoid noise)
    if keywords:
        for keyword in keywords[:5]:
            matches = lookup_concepts_by_synonym(keyword, db_path, threshold=0.7)
            for concept_key, weight in matches:
                # Lower confidence for keyword matches
                concepts_to_assign[concept_key] = max(
                    concepts_to_assign.get(concept_key, 0.0), weight * 0.8
                )

    # 5. Insert into database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    assigned = []
    for concept_key, confidence in concepts_to_assign.items():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO document_semantic_concepts
                (filename, concept_key, confidence, source)
                VALUES (?, ?, ?, ?)
            """,
                (filename, concept_key, confidence, "metadata"),
            )
            assigned.append((concept_key, confidence))
        except sqlite3.IntegrityError:
            # Already exists, update confidence if higher
            cursor.execute(
                """
                UPDATE document_semantic_concepts
                SET confidence = ?, source = ?
                WHERE filename = ? AND concept_key = ?
                AND confidence < ?
            """,
                (confidence, "metadata", filename, concept_key, confidence),
            )

    conn.commit()
    conn.close()

    return assigned


def get_document_concepts(
    filename: str, db_path: str = "data/finagent.db"
) -> list[tuple[str, str, float]]:
    """
    Get all concepts assigned to a document.

    Args:
        filename: Document filename
        db_path: Path to database

    Returns:
        List of (concept_key, concept_name_zh, confidence) tuples
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT dsc.concept_key, sc.name_zh, dsc.confidence
        FROM document_semantic_concepts dsc
        JOIN semantic_concepts sc ON dsc.concept_key = sc.concept_key
        WHERE dsc.filename = ?
        ORDER BY dsc.confidence DESC
    """,
        (filename,),
    )
    results = cursor.fetchall()
    conn.close()
    return results


def get_documents_by_concept(
    concept_key: str, db_path: str = "data/finagent.db", min_confidence: float = 0.5
) -> list[tuple[str, float]]:
    """
    Get all documents tagged with a given concept.

    Args:
        concept_key: Concept key (e.g., "ANTI_MONEY_LAUNDERING")
        db_path: Path to database
        min_confidence: Minimum confidence threshold

    Returns:
        List of (filename, confidence) tuples sorted by confidence descending
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT filename, confidence
        FROM document_semantic_concepts
        WHERE concept_key = ?
        AND confidence >= ?
        ORDER BY confidence DESC
    """,
        (concept_key, min_confidence),
    )
    results = cursor.fetchall()
    conn.close()
    return results


def get_documents_by_concepts(
    concept_keys: list[str], db_path: str = "data/finagent.db", min_confidence: float = 0.5
) -> list[str]:
    """
    Get all documents tagged with ANY of the given concepts.

    Args:
        concept_keys: List of concept keys
        db_path: Path to database
        min_confidence: Minimum confidence threshold

    Returns:
        List of filenames (deduplicated)
    """
    if not concept_keys:
        return []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    placeholders = ", ".join(["?"] * len(concept_keys))
    cursor.execute(
        f"""
        SELECT DISTINCT filename
        FROM document_semantic_concepts
        WHERE concept_key IN ({placeholders})
        AND confidence >= ?
        ORDER BY confidence DESC
    """,
        (*concept_keys, min_confidence),
    )
    filenames = [row[0] for row in cursor.fetchall()]
    conn.close()
    return filenames


def expand_query_with_concepts(
    query_text: str, db_path: str = "data/finagent.db", threshold: float = 0.6
) -> dict:
    """
    Expand user query using semantic concepts.

    Args:
        query_text: User query (e.g., "創投公司裁罰", "銀行洗錢")
        db_path: Path to database
        threshold: Minimum synonym weight threshold

    Returns:
        Dictionary with:
        - original_terms: List of extracted terms from query
        - concepts: List of matched concept keys
        - expanded_terms: List of all synonyms from matched concepts
        - search_keywords: Combined list (original + expanded) for search
        - concept_details: List of (concept_key, concept_name_zh, synonyms) tuples
    """
    # Extract terms from query using jieba for Chinese tokenization
    import re

    import jieba

    # Use jieba for better Chinese word segmentation
    terms = list(jieba.cut(query_text))
    # Filter out single characters and punctuation
    terms = [t.strip() for t in terms if len(t.strip()) >= 2 and re.match(r"[\w]+", t)]

    # Map terms to concepts
    concept_map = {}  # {concept_key: [matched_terms]}
    for term in terms:
        matches = lookup_concepts_by_synonym(term, db_path, threshold)
        for concept_key, weight in matches:
            if concept_key not in concept_map:
                concept_map[concept_key] = []
            concept_map[concept_key].append((term, weight))

    # Get all synonyms for matched concepts
    expanded_terms = []
    concept_details = []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for concept_key in concept_map.keys():
        # Get concept name
        cursor.execute(
            "SELECT name_zh FROM semantic_concepts WHERE concept_key = ?", (concept_key,)
        )
        result = cursor.fetchone()
        concept_name_zh = result[0] if result else concept_key

        # Get all synonyms for this concept
        synonyms = get_all_concept_synonyms(concept_key, db_path)
        expanded_terms.extend(synonyms)

        concept_details.append((concept_key, concept_name_zh, synonyms))

    conn.close()

    # Combine original and expanded terms (deduplicated)
    search_keywords = list(set(terms + expanded_terms))

    return {
        "original_terms": terms,
        "concepts": list(concept_map.keys()),
        "expanded_terms": list(set(expanded_terms)),
        "search_keywords": search_keywords,
        "concept_details": concept_details,
    }


def get_query_concepts_for_filtering(
    query_text: str, db_path: str = "data/finagent.db", threshold: float = 0.6
) -> list[str]:
    """
    Get concept keys for pre-filtering documents based on query.

    This is a simplified version of expand_query_with_concepts that only returns
    concept keys for document filtering.

    Args:
        query_text: User query
        db_path: Path to database
        threshold: Minimum synonym weight threshold

    Returns:
        List of concept keys that match the query
    """
    expansion = expand_query_with_concepts(query_text, db_path, threshold)
    return expansion["concepts"]
