"""Seed semantic concepts and synonyms into database."""

import sqlite3

# Core concept taxonomy
SEMANTIC_CONCEPTS = [
    # Level 1: Domain Categories (Broadest)
    {
        "concept_key": "REGULATORY_COMPLIANCE",
        "concept_level": 1,
        "parent_concept_key": None,
        "name_zh": "法規遵循",
        "name_en": "Regulatory Compliance",
        "description": "法規遵循相關違規與裁罰",
    },
    {
        "concept_key": "FINANCIAL_CRIME",
        "concept_level": 1,
        "parent_concept_key": None,
        "name_zh": "金融犯罪",
        "name_en": "Financial Crime",
        "description": "金融犯罪相關違規",
    },
    {
        "concept_key": "MARKET_INTEGRITY",
        "concept_level": 1,
        "parent_concept_key": None,
        "name_zh": "市場完整性",
        "name_en": "Market Integrity",
        "description": "市場完整性與公平交易",
    },
    {
        "concept_key": "CONSUMER_PROTECTION",
        "concept_level": 1,
        "parent_concept_key": None,
        "name_zh": "消費者保護",
        "name_en": "Consumer Protection",
        "description": "客戶權益與消費者保護",
    },
    {
        "concept_key": "OPERATIONAL_RISK",
        "concept_level": 1,
        "parent_concept_key": None,
        "name_zh": "作業風險",
        "name_en": "Operational Risk",
        "description": "作業風險與內部控制",
    },
    {
        "concept_key": "CORPORATE_GOVERNANCE",
        "concept_level": 1,
        "parent_concept_key": None,
        "name_zh": "公司治理",
        "name_en": "Corporate Governance",
        "description": "公司治理與內部管理",
    },
    # Level 2: Violation Categories (Specific)
    {
        "concept_key": "ANTI_MONEY_LAUNDERING",
        "concept_level": 2,
        "parent_concept_key": "FINANCIAL_CRIME",
        "name_zh": "洗錢防制",
        "name_en": "Anti-Money Laundering",
        "description": "洗錢防制相關違規，包括客戶盡職調查、可疑交易申報等",
    },
    {
        "concept_key": "INSIDER_TRADING",
        "concept_level": 2,
        "parent_concept_key": "MARKET_INTEGRITY",
        "name_zh": "內線交易",
        "name_en": "Insider Trading",
        "description": "內線交易與重大訊息不當使用",
    },
    {
        "concept_key": "INFORMATION_DISCLOSURE",
        "concept_level": 2,
        "parent_concept_key": "MARKET_INTEGRITY",
        "name_zh": "資訊揭露",
        "name_en": "Information Disclosure",
        "description": "資訊揭露義務與財務報告透明度",
    },
    {
        "concept_key": "MARKET_MANIPULATION",
        "concept_level": 2,
        "parent_concept_key": "MARKET_INTEGRITY",
        "name_zh": "市場操縱",
        "name_en": "Market Manipulation",
        "description": "市場操縱、炒作股價等不當交易行為",
    },
    {
        "concept_key": "FRAUD",
        "concept_level": 2,
        "parent_concept_key": "FINANCIAL_CRIME",
        "name_zh": "詐欺",
        "name_en": "Fraud",
        "description": "詐欺、虛偽不實陳述等欺騙行為",
    },
    {
        "concept_key": "CUSTOMER_SUITABILITY",
        "concept_level": 2,
        "parent_concept_key": "CONSUMER_PROTECTION",
        "name_zh": "適合性原則",
        "name_en": "Customer Suitability",
        "description": "客戶適合性原則、投資人保護",
    },
    {
        "concept_key": "RELATED_PARTY_TRANSACTION",
        "concept_level": 2,
        "parent_concept_key": "CORPORATE_GOVERNANCE",
        "name_zh": "關係人交易",
        "name_en": "Related Party Transaction",
        "description": "利害關係人交易、關聯交易",
    },
    {
        "concept_key": "INTERNAL_CONTROL",
        "concept_level": 2,
        "parent_concept_key": "OPERATIONAL_RISK",
        "name_zh": "內部控制",
        "name_en": "Internal Control",
        "description": "內部控制制度缺失",
    },
    {
        "concept_key": "CREDIT_EXTENSION",
        "concept_level": 2,
        "parent_concept_key": "OPERATIONAL_RISK",
        "name_zh": "授信業務",
        "name_en": "Credit Extension",
        "description": "授信業務違規、信用風險管理",
    },
    # Level 3: Entity Categories
    {
        "concept_key": "REGULATORY_AUTHORITY",
        "concept_level": 3,
        "parent_concept_key": None,
        "name_zh": "監管機關",
        "name_en": "Regulatory Authority",
        "description": "政府監管機關",
    },
    {
        "concept_key": "COMMERCIAL_BANK",
        "concept_level": 3,
        "parent_concept_key": None,
        "name_zh": "商業銀行",
        "name_en": "Commercial Bank",
        "description": "商業銀行、本國銀行、外商銀行",
    },
    {
        "concept_key": "SECURITIES_FIRM",
        "concept_level": 3,
        "parent_concept_key": None,
        "name_zh": "證券商",
        "name_en": "Securities Firm",
        "description": "證券商、券商、經紀商",
    },
    {
        "concept_key": "INSURANCE_COMPANY",
        "concept_level": 3,
        "parent_concept_key": None,
        "name_zh": "保險公司",
        "name_en": "Insurance Company",
        "description": "保險公司、壽險、產險",
    },
    {
        "concept_key": "SECURITIES_INVESTMENT_TRUST",
        "concept_level": 3,
        "parent_concept_key": None,
        "name_zh": "證券投資信託",
        "name_en": "Securities Investment Trust",
        "description": "證券投資信託、投信、基金公司",
    },
    {
        "concept_key": "VENTURE_CAPITAL",
        "concept_level": 3,
        "parent_concept_key": None,
        "name_zh": "創業投資",
        "name_en": "Venture Capital",
        "description": "創業投資事業、創投公司",
    },
    {
        "concept_key": "FINANCIAL_HOLDING_COMPANY",
        "concept_level": 3,
        "parent_concept_key": None,
        "name_zh": "金融控股公司",
        "name_en": "Financial Holding Company",
        "description": "金融控股公司、金控",
    },
]

# Concept synonyms mapping
CONCEPT_SYNONYMS = {
    "ANTI_MONEY_LAUNDERING": [
        ("洗錢", "zh", 1.0),
        ("洗錢防制", "zh", 1.0),
        ("洗錢防制法", "zh", 0.9),
        ("洗錢防制作業", "zh", 0.9),
        ("洗錢防制缺失", "zh", 0.9),
        ("反洗錢", "zh", 1.0),
        ("AML", "en", 1.0),
        ("Anti-Money Laundering", "en", 1.0),
        ("可疑交易", "zh", 0.7),
        ("可疑交易申報", "zh", 0.7),
        ("疑似洗錢", "zh", 0.8),
        ("KYC", "en", 0.6),
        ("客戶盡職調查", "zh", 0.6),
        ("認識客戶", "zh", 0.6),
    ],
    "INSIDER_TRADING": [
        ("內線", "zh", 1.0),
        ("內線交易", "zh", 1.0),
        ("內部人交易", "zh", 0.9),
        ("內部交易", "zh", 0.9),
        ("insider trading", "en", 1.0),
        ("insider", "en", 0.8),
        ("重大訊息", "zh", 0.7),
        ("重大消息", "zh", 0.7),
        ("內部消息", "zh", 0.7),
        ("內幕交易", "zh", 0.9),
    ],
    "INFORMATION_DISCLOSURE": [
        ("資訊揭露", "zh", 1.0),
        ("資訊公開", "zh", 0.9),
        ("訊息揭露", "zh", 0.9),
        ("財報揭露", "zh", 0.8),
        ("財務報告揭露", "zh", 0.8),
        ("揭露義務", "zh", 0.8),
        ("disclosure", "en", 1.0),
        ("information disclosure", "en", 1.0),
        ("transparency", "en", 0.7),
        ("財務報告", "zh", 0.6),
        ("年報", "zh", 0.5),
    ],
    "MARKET_MANIPULATION": [
        ("市場操縱", "zh", 1.0),
        ("操縱股價", "zh", 0.9),
        ("炒作", "zh", 0.8),
        ("market manipulation", "en", 1.0),
        ("manipulation", "en", 0.8),
        ("不當交易", "zh", 0.7),
        ("聯合操縱", "zh", 0.9),
    ],
    "FRAUD": [
        ("詐欺", "zh", 1.0),
        ("欺詐", "zh", 1.0),
        ("fraud", "en", 1.0),
        ("詐騙", "zh", 0.9),
        ("不實陳述", "zh", 0.8),
        ("虛偽", "zh", 0.7),
        ("虛偽記載", "zh", 0.8),
        ("偽造", "zh", 0.7),
    ],
    "CUSTOMER_SUITABILITY": [
        ("適合性", "zh", 1.0),
        ("適合性原則", "zh", 1.0),
        ("客戶適合性", "zh", 1.0),
        ("suitability", "en", 1.0),
        ("投資人保護", "zh", 0.7),
        ("客戶權益", "zh", 0.6),
        ("專業投資人", "zh", 0.6),
    ],
    "RELATED_PARTY_TRANSACTION": [
        ("關係人交易", "zh", 1.0),
        ("利害關係人", "zh", 1.0),
        ("利害關係人交易", "zh", 1.0),
        ("關聯交易", "zh", 0.9),
        ("related party", "en", 1.0),
        ("related party transaction", "en", 1.0),
        ("關係企業", "zh", 0.7),
    ],
    "INTERNAL_CONTROL": [
        ("內部控制", "zh", 1.0),
        ("內控", "zh", 0.9),
        ("內控制度", "zh", 0.9),
        ("internal control", "en", 1.0),
        ("內部控制制度", "zh", 1.0),
        ("內部稽核", "zh", 0.7),
        ("稽核", "zh", 0.6),
    ],
    "CREDIT_EXTENSION": [
        ("授信", "zh", 1.0),
        ("授信業務", "zh", 1.0),
        ("信用貸款", "zh", 0.8),
        ("lending", "en", 0.8),
        ("credit extension", "en", 1.0),
        ("貸款", "zh", 0.7),
        ("放款", "zh", 0.8),
    ],
    "COMMERCIAL_BANK": [
        ("銀行", "zh", 1.0),
        ("商業銀行", "zh", 1.0),
        ("bank", "en", 1.0),
        ("commercial bank", "en", 1.0),
        ("銀行業", "zh", 0.9),
        ("本國銀行", "zh", 0.9),
        ("外商銀行", "zh", 0.9),
    ],
    "SECURITIES_FIRM": [
        ("證券商", "zh", 1.0),
        ("證券公司", "zh", 1.0),
        ("券商", "zh", 0.9),
        ("securities firm", "en", 1.0),
        ("securities company", "en", 1.0),
        ("broker", "en", 0.8),
        ("brokerage", "en", 0.8),
        ("綜合證券", "zh", 0.8),
    ],
    "INSURANCE_COMPANY": [
        ("保險公司", "zh", 1.0),
        ("保險", "zh", 0.9),
        ("insurance company", "en", 1.0),
        ("insurer", "en", 0.9),
        ("壽險", "zh", 0.8),
        ("產險", "zh", 0.8),
        ("人壽保險", "zh", 0.9),
        ("財產保險", "zh", 0.9),
    ],
    "SECURITIES_INVESTMENT_TRUST": [
        ("證券投資信託", "zh", 1.0),
        ("投信", "zh", 1.0),
        ("證券投信", "zh", 1.0),
        ("investment trust", "en", 1.0),
        ("基金公司", "zh", 0.8),
        ("投資信託", "zh", 0.9),
    ],
    "VENTURE_CAPITAL": [
        ("創投", "zh", 1.0),
        ("創業投資", "zh", 1.0),
        ("創投公司", "zh", 1.0),
        ("創業投資事業", "zh", 1.0),
        ("創業投資公司", "zh", 1.0),
        ("VC", "en", 1.0),
        ("venture capital", "en", 1.0),
    ],
    "FINANCIAL_HOLDING_COMPANY": [
        ("金控", "zh", 1.0),
        ("金融控股", "zh", 1.0),
        ("金融控股公司", "zh", 1.0),
        ("金控公司", "zh", 1.0),
        ("financial holding", "en", 1.0),
        ("金控法", "zh", 0.8),
    ],
    "REGULATORY_AUTHORITY": [
        ("金管會", "zh", 1.0),
        ("金融監督管理委員會", "zh", 1.0),
        ("FSC", "en", 1.0),
        ("中央銀行", "zh", 1.0),
        ("央行", "zh", 0.9),
        ("公平會", "zh", 1.0),
        ("公平交易委員會", "zh", 1.0),
        ("銀行局", "zh", 1.0),
        ("證期局", "zh", 1.0),
        ("證券期貨局", "zh", 1.0),
        ("保險局", "zh", 1.0),
    ],
}


def seed_semantic_concepts(db_path: str = "data/finagent.db"):
    """
    Seed semantic concepts and synonyms into database.

    Args:
        db_path: Path to SQLite database
    """
    print(f"Seeding semantic concepts to {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert concepts
    print(f"\nInserting {len(SEMANTIC_CONCEPTS)} concepts...")
    for concept in SEMANTIC_CONCEPTS:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO semantic_concepts
                (concept_key, concept_level, parent_concept_key, name_zh, name_en, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    concept["concept_key"],
                    concept["concept_level"],
                    concept["parent_concept_key"],
                    concept["name_zh"],
                    concept["name_en"],
                    concept["description"],
                ),
            )
            print(f"  ✓ {concept['concept_key']} ({concept['name_zh']})")
        except Exception as e:
            print(f"  ✗ Failed to insert {concept['concept_key']}: {e}")

    conn.commit()

    # Insert synonyms
    total_synonyms = sum(len(synonyms) for synonyms in CONCEPT_SYNONYMS.values())
    print(f"\nInserting {total_synonyms} synonyms...")

    for concept_key, synonyms in CONCEPT_SYNONYMS.items():
        print(f"\n  {concept_key}:")
        for synonym, syn_type, weight in synonyms:
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO concept_synonyms
                    (concept_key, synonym, synonym_type, weight)
                    VALUES (?, ?, ?, ?)
                    """,
                    (concept_key, synonym, syn_type, weight),
                )
                print(f"    + {synonym} ({syn_type}, {weight})")
            except Exception as e:
                print(f"    ✗ Failed to insert synonym '{synonym}': {e}")

    conn.commit()

    # Verify counts
    cursor.execute("SELECT COUNT(*) FROM semantic_concepts")
    concept_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM concept_synonyms")
    synonym_count = cursor.fetchone()[0]

    conn.close()

    print("\n✓ Seeding complete!")
    print(f"  Concepts: {concept_count}")
    print(f"  Synonyms: {synonym_count}")


if __name__ == "__main__":
    seed_semantic_concepts()
