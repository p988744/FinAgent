/**
 * WikiPage - Financial Legal Knowledge Base
 *
 * A comprehensive knowledge explorer for learning about:
 * - Penalty Cases (裁罰案件)
 * - Legal Provisions (原始法條)
 * - Regulatory Bodies & Institutions
 */

import React, { useState, useEffect, useCallback } from 'react';

// Types
interface WikiOverview {
  total_documents: number;
  total_categories: number;
  categories_by_type: {
    authority: number;
    institution: number;
    violation: number;
  };
  document_stats: {
    total_documents: number;
    with_metadata: number;
    without_metadata: number;
    by_type: Record<string, number>;
    by_authority: Record<string, number>;
    avg_confidence: number;
  };
  recent_documents: WikiDocument[];
}

interface Category {
  id: number;
  name: string;
  type: string;
  document_count: number;
  description: string;
  keywords: string[];
}

interface WikiDocument {
  doc_id: string;
  filename: string;
  document_type: string | null;
  issuing_authority: string | null;
  date: string | null;
  related_institutions: string[];
  violation_types: string[];
  extraction_confidence: number | null;
}

interface TopEntity {
  name: string;
  count: number;
}

// 構成要件 (Constitutive Elements) - Links violations to legal provisions
interface ConstitutiveElement {
  id: string;
  element_name: string;  // 要件名稱
  description: string;   // 要件說明
  required: boolean;     // 是否為必要要件
}

// Mock data for legal provisions with 構成要件
interface LegalProvision {
  id: string;
  law_name: string;
  article: string;
  content: string;
  category: string;
  related_violations: string[];
  constitutive_elements: ConstitutiveElement[];  // 構成要件
  penalty_range?: string;  // 罰則範圍
  authority: string;  // 主管機關
}

// 違規類型與法律依據的對照 (Violation-to-Law Mapping)
interface ViolationLegalBasis {
  violation_type: string;
  provisions: {
    provision_id: string;
    law_name: string;
    article: string;
    relevance: 'primary' | 'secondary';  // 主要/次要法源
  }[];
  common_elements: string[];  // 常見構成要件
  typical_penalties: string[];  // 常見處分
}

const MOCK_PROVISIONS: LegalProvision[] = [
  {
    id: 'banking-act-45',
    law_name: '銀行法',
    article: '第45條',
    content: '銀行違反法令、章程或有礙健全經營之虞時，主管機關除得予以糾正、命其限期改善外，並得視情節之輕重，為下列處分：一、撤銷法定會議之決議。二、廢止許可。三、停止營業之全部或一部。四、撤換經理人或職員。五、解除董事、監察人職務或停止其於一定期間內執行職務。六、其他必要之處置。',
    category: '銀行監理',
    related_violations: ['內控缺失', '法令遵循', '資本適足'],
    authority: '金管會銀行局',
    penalty_range: '糾正、限期改善、撤銷決議、廢止許可、停止營業',
    constitutive_elements: [
      { id: 'ba45-1', element_name: '違反法令', description: '銀行之行為違反銀行法或相關金融法規', required: true },
      { id: 'ba45-2', element_name: '違反章程', description: '銀行之行為違反其公司章程規定', required: false },
      { id: 'ba45-3', element_name: '有礙健全經營', description: '銀行之行為可能危及其財務健全性或經營穩定性', required: false },
    ],
  },
  {
    id: 'banking-act-61',
    law_name: '銀行法',
    article: '第61條之1',
    content: '銀行辦理授信業務，應依借款人之信用狀況、資金用途、還款來源、擔保品價值及其償債能力，核貸適當金額。銀行對同一人、同一關係人或同一關係企業之授信，應建立適當之風險控管機制。',
    category: '授信業務',
    related_violations: ['授信違規', '擔保品評估', '徵信不實'],
    authority: '金管會銀行局',
    penalty_range: '依第129條處新臺幣200萬至1000萬元罰鍰',
    constitutive_elements: [
      { id: 'ba61-1', element_name: '信用狀況評估不實', description: '未依規定確實評估借款人之信用狀況', required: true },
      { id: 'ba61-2', element_name: '擔保品價值評估不當', description: '擔保品估值過高或評估程序有缺失', required: false },
      { id: 'ba61-3', element_name: '償債能力審查不足', description: '未充分評估借款人之還款能力', required: false },
      { id: 'ba61-4', element_name: '風險控管機制不健全', description: '對同一人或關係企業授信缺乏適當控管', required: false },
    ],
  },
  {
    id: 'aml-act-7',
    law_name: '洗錢防制法',
    article: '第7條',
    content: '金融機構及指定之非金融事業或人員應進行確認客戶身分程序，並留存其確認客戶身分程序所得資料。前項確認客戶身分程序應以風險基礎方法辦理，對於高風險情形應加強確認客戶身分。',
    category: '洗錢防制',
    related_violations: ['KYC缺失', '可疑交易申報', '客戶審查'],
    authority: '金管會、法務部調查局',
    penalty_range: '依第14條處新臺幣50萬至1000萬元罰鍰',
    constitutive_elements: [
      { id: 'aml7-1', element_name: '未進行客戶身分確認', description: '未依規定對客戶進行身分驗證程序', required: true },
      { id: 'aml7-2', element_name: '未留存確認資料', description: '未保存客戶身分確認程序所得之相關文件', required: true },
      { id: 'aml7-3', element_name: '未採風險基礎方法', description: '未依客戶風險等級採取相應之確認措施', required: false },
      { id: 'aml7-4', element_name: '高風險客戶未加強審查', description: '對高風險客戶未執行加強客戶審查程序', required: false },
    ],
  },
  {
    id: 'securities-act-171',
    law_name: '證券交易法',
    article: '第171條',
    content: '有下列情事之一者，處三年以上十年以下有期徒刑，得併科新臺幣一千萬元以上二億元以下罰金：一、違反第155條第1項或第2項規定。二、違反第157條之1第1項規定。',
    category: '證券監理',
    related_violations: ['內線交易', '操縱市場', '財報不實'],
    authority: '金管會證期局',
    penalty_range: '三年以上十年以下有期徒刑，得併科1000萬至2億元罰金',
    constitutive_elements: [
      { id: 'sa171-1', element_name: '具內部人身分', description: '行為人須為公司內部人或準內部人', required: true },
      { id: 'sa171-2', element_name: '知悉重大消息', description: '獲知足以影響股價之重大消息', required: true },
      { id: 'sa171-3', element_name: '消息未公開', description: '該重大消息尚未對外公開揭露', required: true },
      { id: 'sa171-4', element_name: '買賣證券行為', description: '有買入或賣出該公司股票之行為', required: true },
    ],
  },
  {
    id: 'insurance-act-149',
    law_name: '保險法',
    article: '第149條',
    content: '保險業違反法令、章程或有礙健全經營之虞時，主管機關除得予以糾正或命其限期改善外，並得視情節輕重，為下列處分：一、限制其資金之運用。二、命其增資。三、命其處分特定資產。四、限制或禁止其轉投資。',
    category: '保險監理',
    related_violations: ['招攬違規', '理賠爭議', '準備金不足'],
    authority: '金管會保險局',
    penalty_range: '糾正、限期改善、限制資金運用、命增資、命處分資產',
    constitutive_elements: [
      { id: 'ia149-1', element_name: '違反法令', description: '保險業之行為違反保險法或相關法規', required: true },
      { id: 'ia149-2', element_name: '違反章程', description: '保險業之行為違反其公司章程', required: false },
      { id: 'ia149-3', element_name: '有礙健全經營', description: '保險業之行為可能危及財務健全性', required: false },
    ],
  },
  {
    id: 'aml-act-10',
    law_name: '洗錢防制法',
    article: '第10條',
    content: '金融機構及指定之非金融事業或人員對於達一定金額以上之通貨交易，應確認客戶身分及留存交易紀錄，並應向法務部調查局申報。',
    category: '洗錢防制',
    related_violations: ['大額交易申報', '交易紀錄保存'],
    authority: '法務部調查局',
    penalty_range: '依第14條處新臺幣50萬至1000萬元罰鍰',
    constitutive_elements: [
      { id: 'aml10-1', element_name: '達申報門檻之交易', description: '通貨交易金額達50萬元以上', required: true },
      { id: 'aml10-2', element_name: '未確認客戶身分', description: '未對交易客戶進行身分確認程序', required: false },
      { id: 'aml10-3', element_name: '未申報交易', description: '未依規定向調查局申報大額交易', required: true },
    ],
  },
];

// 違規類型與構成要件對照表
const VIOLATION_LEGAL_BASIS: ViolationLegalBasis[] = [
  {
    violation_type: '洗錢防制缺失',
    provisions: [
      { provision_id: 'aml-act-7', law_name: '洗錢防制法', article: '第7條', relevance: 'primary' },
      { provision_id: 'aml-act-10', law_name: '洗錢防制法', article: '第10條', relevance: 'secondary' },
    ],
    common_elements: ['未進行客戶身分確認', '未留存確認資料', '高風險客戶未加強審查'],
    typical_penalties: ['罰鍰50萬至1000萬元', '限期改善', '停止營業'],
  },
  {
    violation_type: '授信違規',
    provisions: [
      { provision_id: 'banking-act-61', law_name: '銀行法', article: '第61條之1', relevance: 'primary' },
      { provision_id: 'banking-act-45', law_name: '銀行法', article: '第45條', relevance: 'secondary' },
    ],
    common_elements: ['信用狀況評估不實', '擔保品價值評估不當', '風險控管機制不健全'],
    typical_penalties: ['罰鍰200萬至1000萬元', '糾正', '撤換經理人'],
  },
  {
    violation_type: '內線交易',
    provisions: [
      { provision_id: 'securities-act-171', law_name: '證券交易法', article: '第171條', relevance: 'primary' },
    ],
    common_elements: ['具內部人身分', '知悉重大消息', '消息未公開', '買賣證券行為'],
    typical_penalties: ['三年以上十年以下有期徒刑', '罰金1000萬至2億元'],
  },
  {
    violation_type: '內控缺失',
    provisions: [
      { provision_id: 'banking-act-45', law_name: '銀行法', article: '第45條', relevance: 'primary' },
    ],
    common_elements: ['違反法令', '有礙健全經營'],
    typical_penalties: ['糾正', '限期改善', '撤換經理人'],
  },
  {
    violation_type: '保險招攬違規',
    provisions: [
      { provision_id: 'insurance-act-149', law_name: '保險法', article: '第149條', relevance: 'primary' },
    ],
    common_elements: ['違反法令', '有礙健全經營'],
    typical_penalties: ['糾正', '限制資金運用', '命增資'],
  },
];

// Knowledge concepts for learning
interface KnowledgeConcept {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  relatedCount: number;
}

const KNOWLEDGE_CONCEPTS: KnowledgeConcept[] = [
  {
    id: 'aml',
    title: '洗錢防制',
    description: '了解金融機構如何防範洗錢行為，包括KYC程序、可疑交易申報等監理要求',
    icon: 'shield',
    color: 'amber',
    relatedCount: 15,
  },
  {
    id: 'credit',
    title: '授信管理',
    description: '探索銀行授信業務的規範，包括徵信程序、擔保品評估、風險控管等',
    icon: 'credit-card',
    color: 'emerald',
    relatedCount: 12,
  },
  {
    id: 'insider',
    title: '內線交易',
    description: '學習證券市場內線交易的認定標準、法律責任與相關判例',
    icon: 'chart-bar',
    color: 'rose',
    relatedCount: 8,
  },
  {
    id: 'consumer',
    title: '消費者保護',
    description: '了解金融消費者保護相關法規與金融機構的義務',
    icon: 'user-group',
    color: 'sky',
    relatedCount: 10,
  },
  {
    id: 'info-security',
    title: '資訊安全',
    description: '探索金融機構資訊安全規範、個資保護與系統安全要求',
    icon: 'lock-closed',
    color: 'violet',
    relatedCount: 7,
  },
  {
    id: 'compliance',
    title: '法令遵循',
    description: '了解金融機構內部控制、法令遵循制度的建立與運作',
    icon: 'clipboard-check',
    color: 'cyan',
    relatedCount: 20,
  },
];

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

type ViewMode = 'overview' | 'cases' | 'laws' | 'concepts' | 'elements';

export function WikiPage() {
  // State
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [overview, setOverview] = useState<WikiOverview | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [documents, setDocuments] = useState<WikiDocument[]>([]);
  const [topAuthorities, setTopAuthorities] = useState<TopEntity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryType, setSelectedCategoryType] = useState<'authority' | 'institution' | 'violation'>('authority');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<WikiDocument | null>(null);
  const [selectedProvision, setSelectedProvision] = useState<LegalProvision | null>(null);
  const [selectedConcept, setSelectedConcept] = useState<KnowledgeConcept | null>(null);
  const [selectedViolationBasis, setSelectedViolationBasis] = useState<ViolationLegalBasis | null>(null);

  // API calls
  const fetchOverview = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/wiki/overview`);
      if (!response.ok) throw new Error('Failed to fetch overview');
      const data = await response.json();
      setOverview(data);
      if (data.recent_documents) {
        setDocuments(data.recent_documents);
      }
      if (data.document_stats?.by_authority) {
        const authorities = Object.entries(data.document_stats.by_authority)
          .map(([name, count]) => ({ name, count: count as number }))
          .sort((a, b) => b.count - a.count);
        setTopAuthorities(authorities);
      }
    } catch (err) {
      console.error('Failed to fetch overview:', err);
    }
  }, []);

  const fetchCategories = useCallback(async (type: 'authority' | 'institution' | 'violation') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/wiki/categories?type=${type}`);
      if (!response.ok) throw new Error('Failed to fetch categories');
      const data = await response.json();
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  }, []);

  const fetchDocuments = useCallback(async (categoryName?: string, categoryType?: string) => {
    try {
      let url = `${API_BASE_URL}/api/v1/wiki/documents`;
      if (categoryName && categoryType) {
        url += `?category=${encodeURIComponent(categoryName)}&type=${categoryType}`;
      }
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await fetchOverview();
      await fetchCategories(selectedCategoryType);
      setIsLoading(false);
    };
    loadData();
  }, [fetchOverview, fetchCategories, selectedCategoryType]);

  useEffect(() => {
    if (selectedCategory) {
      fetchDocuments(selectedCategory, selectedCategoryType);
    }
  }, [selectedCategory, selectedCategoryType, fetchDocuments]);

  // Helpers
  const formatDate = (dateString: string | null): string => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('zh-TW');
  };

  const filteredDocuments = searchQuery.trim()
    ? documents.filter(doc =>
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.issuing_authority?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.related_institutions?.some(inst => inst.toLowerCase().includes(searchQuery.toLowerCase())) ||
        doc.violation_types?.some(vt => vt.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : documents;

  const filteredProvisions = searchQuery.trim()
    ? MOCK_PROVISIONS.filter(p =>
        p.law_name.includes(searchQuery) ||
        p.article.includes(searchQuery) ||
        p.content.includes(searchQuery) ||
        p.category.includes(searchQuery)
      )
    : MOCK_PROVISIONS;

  // Icon component
  const ConceptIcon = ({ name, className }: { name: string; className?: string }) => {
    const icons: Record<string, JSX.Element> = {
      shield: (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      'credit-card': (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      ),
      'chart-bar': (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      'user-group': (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      'lock-closed': (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      'clipboard-check': (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      ),
    };
    return icons[name] || null;
  };

  return (
    <div className="min-h-screen bg-slate-950 bg-grid">
      {/* Navigation */}
      <nav className="border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
                  <svg className="w-5 h-5 text-slate-950" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-lg font-serif font-semibold text-slate-50">FinAgent</h1>
                  <p className="text-xs text-slate-500">金融法律知識庫</p>
                </div>
              </a>
            </div>
            <div className="flex items-center gap-3">
              <a href="/" className="btn btn-ghost text-sm">研究查詢</a>
              <a href="/documents" className="btn btn-ghost text-sm">文件管理</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="border-b border-slate-800/50 bg-gradient-to-b from-slate-900/50 to-transparent">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="max-w-3xl">
            <h2 className="text-4xl font-serif font-bold text-slate-50 mb-4">
              金融法律<span className="text-gradient">知識庫</span>
            </h2>
            <p className="text-lg text-slate-400 mb-8">
              探索台灣金融監理法規、裁罰案例與法律知識。從實務案例中學習，深入了解金融法規的應用與解釋。
            </p>

            {/* View Mode Tabs */}
            <div className="flex flex-wrap gap-3">
              {[
                { mode: 'overview' as ViewMode, label: '總覽', icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' },
                { mode: 'cases' as ViewMode, label: '裁罰案件', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
                { mode: 'elements' as ViewMode, label: '構成要件', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
                { mode: 'laws' as ViewMode, label: '法規條文', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
                { mode: 'concepts' as ViewMode, label: '知識概念', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
              ].map(({ mode, label, icon }) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    viewMode === mode
                      ? 'bg-amber-500/20 text-amber-200 border border-amber-500/30'
                      : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800 border border-transparent'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
                  </svg>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Search Bar */}
      <div className="max-w-7xl mx-auto px-6 -mt-6 mb-8 relative z-10">
        <div className="card p-4">
          <div className="relative">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder={
                viewMode === 'cases' ? '搜尋案例、機構、違規類型...' :
                viewMode === 'elements' ? '搜尋違規類型、構成要件...' :
                viewMode === 'laws' ? '搜尋法規名稱、條號、內容...' :
                viewMode === 'concepts' ? '搜尋知識概念...' :
                '搜尋知識庫...'
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-12 text-lg"
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 pb-12">
        {/* Overview Mode */}
        {viewMode === 'overview' && (
          <div className="space-y-8">
            {/* Stats Grid */}
            {overview && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card p-5 hover:border-amber-500/30 transition-colors cursor-pointer" onClick={() => setViewMode('cases')}>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                      <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">裁罰案件</p>
                      <p className="text-2xl font-mono font-semibold text-slate-100">{overview.total_documents}</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5 hover:border-emerald-500/30 transition-colors cursor-pointer" onClick={() => setViewMode('laws')}>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                      <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">法規條文</p>
                      <p className="text-2xl font-mono font-semibold text-slate-100">{MOCK_PROVISIONS.length}</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5 hover:border-sky-500/30 transition-colors cursor-pointer" onClick={() => setViewMode('concepts')}>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center">
                      <svg className="w-6 h-6 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">知識概念</p>
                      <p className="text-2xl font-mono font-semibold text-slate-100">{KNOWLEDGE_CONCEPTS.length}</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-rose-500/10 flex items-center justify-center">
                      <svg className="w-6 h-6 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">監理機關</p>
                      <p className="text-2xl font-mono font-semibold text-slate-100">{overview.categories_by_type?.authority || 0}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Knowledge Concepts Grid */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-serif font-semibold text-slate-100">熱門知識主題</h3>
                <button onClick={() => setViewMode('concepts')} className="text-sm text-amber-400 hover:text-amber-300">
                  查看全部 &rarr;
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {KNOWLEDGE_CONCEPTS.slice(0, 6).map((concept) => (
                  <div
                    key={concept.id}
                    className="card p-5 hover:border-slate-700 transition-all cursor-pointer group"
                    onClick={() => setSelectedConcept(concept)}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`w-10 h-10 rounded-xl bg-${concept.color}-500/10 flex items-center justify-center flex-shrink-0`}>
                        <ConceptIcon name={concept.icon} className={`w-5 h-5 text-${concept.color}-400`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-base font-medium text-slate-200 mb-1 group-hover:text-amber-200 transition-colors">
                          {concept.title}
                        </h4>
                        <p className="text-sm text-slate-500 line-clamp-2">{concept.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="badge badge-slate">{concept.relatedCount} 相關案例</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Cases */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-serif font-semibold text-slate-100">近期裁罰案件</h3>
                <button onClick={() => setViewMode('cases')} className="text-sm text-amber-400 hover:text-amber-300">
                  查看全部 &rarr;
                </button>
              </div>
              <div className="card">
                <div className="divide-y divide-slate-800/50">
                  {documents.slice(0, 5).map((doc) => (
                    <div
                      key={doc.doc_id}
                      className="p-4 hover:bg-slate-800/20 transition-colors cursor-pointer"
                      onClick={() => setSelectedDocument(doc)}
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0">
                          <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-slate-200 truncate mb-1">{doc.filename}</h4>
                          <div className="flex flex-wrap items-center gap-2">
                            {doc.issuing_authority && <span className="badge badge-amber">{doc.issuing_authority}</span>}
                            {doc.violation_types?.slice(0, 1).map((vt, i) => (
                              <span key={i} className="badge badge-rose">{vt}</span>
                            ))}
                            <span className="text-xs text-slate-500">{formatDate(doc.date)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Key Legal Provisions */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-serif font-semibold text-slate-100">重要法規條文</h3>
                <button onClick={() => setViewMode('laws')} className="text-sm text-amber-400 hover:text-amber-300">
                  查看全部 &rarr;
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {MOCK_PROVISIONS.slice(0, 4).map((provision) => (
                  <div
                    key={provision.id}
                    className="card p-5 hover:border-emerald-500/30 transition-all cursor-pointer"
                    onClick={() => setSelectedProvision(provision)}
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-slate-200">{provision.law_name}</h4>
                        <p className="text-xs text-emerald-400">{provision.article}</p>
                      </div>
                    </div>
                    <p className="text-sm text-slate-400 line-clamp-2 mb-3">{provision.content}</p>
                    <div className="flex flex-wrap gap-1">
                      {provision.related_violations.slice(0, 2).map((v, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">{v}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Cases Mode */}
        {viewMode === 'cases' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Sidebar */}
            <div className="lg:col-span-4 space-y-6">
              <div className="card">
                <div className="p-4 border-b border-slate-800/50">
                  <h3 className="text-base font-serif font-semibold text-slate-100 mb-3">分類瀏覽</h3>
                  <div className="flex gap-2">
                    {(['authority', 'institution', 'violation'] as const).map((type) => (
                      <button
                        key={type}
                        onClick={() => {
                          setSelectedCategoryType(type);
                          setSelectedCategory(null);
                        }}
                        className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                          selectedCategoryType === type
                            ? 'bg-amber-500/20 text-amber-200 border border-amber-500/30'
                            : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
                        }`}
                      >
                        {type === 'authority' ? '監理機關' : type === 'institution' ? '金融機構' : '違規類型'}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="p-3 max-h-[400px] overflow-y-auto scrollbar-hide">
                  <button
                    onClick={() => setSelectedCategory(null)}
                    className={`w-full text-left p-3 rounded-lg mb-1 transition-colors ${
                      !selectedCategory ? 'bg-amber-500/10 text-amber-200' : 'text-slate-300 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm">全部案件</span>
                      <span className="text-xs text-slate-500">{overview?.total_documents || 0}</span>
                    </div>
                  </button>
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category.name)}
                      className={`w-full text-left p-3 rounded-lg mb-1 transition-colors ${
                        selectedCategory === category.name ? 'bg-amber-500/10 text-amber-200' : 'text-slate-300 hover:bg-slate-800/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm">{category.name}</span>
                        <span className="text-xs text-slate-500">{category.document_count}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {topAuthorities.length > 0 && (
                <div className="card">
                  <div className="p-4 border-b border-slate-800/50">
                    <h3 className="text-base font-serif font-semibold text-slate-100">監理機關統計</h3>
                  </div>
                  <div className="p-3">
                    {topAuthorities.slice(0, 5).map((auth) => (
                      <div key={auth.name} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-800/30">
                        <span className="text-sm text-slate-300">{auth.name}</span>
                        <span className="badge badge-slate">{auth.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Document List */}
            <div className="lg:col-span-8">
              <div className="card">
                <div className="p-5 border-b border-slate-800/50">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-serif font-semibold text-slate-100">
                      {searchQuery ? '搜尋結果' : selectedCategory ? '分類案件' : '全部裁罰案件'}
                    </h3>
                    <span className="badge badge-slate">{filteredDocuments.length} 筆</span>
                  </div>
                </div>

                {isLoading ? (
                  <div className="p-12 flex flex-col items-center justify-center">
                    <svg className="w-8 h-8 text-amber-400 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <p className="text-slate-400">載入中...</p>
                  </div>
                ) : filteredDocuments.length === 0 ? (
                  <div className="p-12 flex flex-col items-center justify-center">
                    <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                      <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <p className="text-slate-400">無符合條件的案件</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800/50">
                    {filteredDocuments.map((doc) => (
                      <div
                        key={doc.doc_id}
                        className="p-4 hover:bg-slate-800/20 transition-colors cursor-pointer"
                        onClick={() => setSelectedDocument(doc)}
                      >
                        <div className="flex items-start gap-4">
                          <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0">
                            <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-slate-200 truncate mb-1">{doc.filename}</h4>
                            <div className="flex flex-wrap items-center gap-2 mb-2">
                              {doc.issuing_authority && <span className="badge badge-amber">{doc.issuing_authority}</span>}
                              {doc.related_institutions?.slice(0, 2).map((inst, i) => (
                                <span key={i} className="badge badge-slate">{inst}</span>
                              ))}
                              {doc.violation_types?.slice(0, 1).map((vt, i) => (
                                <span key={i} className="badge badge-rose">{vt}</span>
                              ))}
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span>{formatDate(doc.date)}</span>
                              {doc.document_type && <span>{doc.document_type}</span>}
                              {doc.extraction_confidence !== null && (
                                <span className="text-emerald-500">
                                  {(doc.extraction_confidence * 100).toFixed(0)}% 信心度
                                </span>
                              )}
                            </div>
                          </div>
                          <svg className="w-4 h-4 text-slate-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Laws Mode */}
        {viewMode === 'laws' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredProvisions.map((provision) => (
                <div
                  key={provision.id}
                  className="card p-5 hover:border-emerald-500/30 transition-all cursor-pointer"
                  onClick={() => setSelectedProvision(provision)}
                >
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-base font-medium text-slate-200">{provision.law_name}</h4>
                      <p className="text-sm text-emerald-400">{provision.article}</p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-400 line-clamp-3 mb-4">{provision.content}</p>
                  <div className="flex items-center justify-between">
                    <span className="badge badge-emerald">{provision.category}</span>
                    <span className="text-xs text-slate-500">{provision.related_violations.length} 相關違規</span>
                  </div>
                </div>
              ))}
            </div>

            {filteredProvisions.length === 0 && (
              <div className="card p-12 flex flex-col items-center justify-center">
                <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <p className="text-slate-400">無符合條件的法規條文</p>
              </div>
            )}
          </div>
        )}

        {/* Concepts Mode */}
        {viewMode === 'concepts' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {KNOWLEDGE_CONCEPTS.map((concept) => (
              <div
                key={concept.id}
                className={`card p-6 hover:border-${concept.color}-500/30 transition-all cursor-pointer group`}
                onClick={() => setSelectedConcept(concept)}
              >
                <div className={`w-14 h-14 rounded-xl bg-${concept.color}-500/10 flex items-center justify-center mb-4`}>
                  <ConceptIcon name={concept.icon} className={`w-7 h-7 text-${concept.color}-400`} />
                </div>
                <h4 className={`text-xl font-serif font-semibold text-slate-200 mb-2 group-hover:text-${concept.color}-200 transition-colors`}>
                  {concept.title}
                </h4>
                <p className="text-sm text-slate-400 mb-4">{concept.description}</p>
                <div className="flex items-center justify-between pt-4 border-t border-slate-800/50">
                  <span className="badge badge-slate">{concept.relatedCount} 相關案例</span>
                  <svg className={`w-4 h-4 text-slate-600 group-hover:text-${concept.color}-400 transition-colors`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Elements Mode - 構成要件 */}
        {viewMode === 'elements' && (
          <div className="space-y-8">
            {/* Introduction */}
            <div className="card p-6 bg-gradient-to-r from-violet-500/5 to-purple-500/5 border-violet-500/20">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-serif font-semibold text-slate-100 mb-2">什麼是構成要件？</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    構成要件是指法律規定中，必須滿足的各項條件才能成立該違規行為。了解構成要件有助於：
                    <span className="text-violet-300">（1）判斷行為是否違法</span>、
                    <span className="text-violet-300">（2）預防潛在違規風險</span>、
                    <span className="text-violet-300">（3）理解裁罰依據</span>。
                  </p>
                </div>
              </div>
            </div>

            {/* Violation Types Grid */}
            <div>
              <h3 className="text-xl font-serif font-semibold text-slate-100 mb-4">違規類型與構成要件對照</h3>
              <div className="space-y-4">
                {VIOLATION_LEGAL_BASIS
                  .filter(v => !searchQuery.trim() ||
                    v.violation_type.includes(searchQuery) ||
                    v.common_elements.some(e => e.includes(searchQuery))
                  )
                  .map((violation) => (
                  <div
                    key={violation.violation_type}
                    className="card overflow-hidden hover:border-violet-500/30 transition-all cursor-pointer"
                    onClick={() => setSelectedViolationBasis(violation)}
                  >
                    <div className="p-5">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center flex-shrink-0">
                          <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <h4 className="text-base font-medium text-slate-100 mb-2">{violation.violation_type}</h4>

                          {/* Legal Basis */}
                          <div className="flex flex-wrap gap-2 mb-3">
                            {violation.provisions.map((p, idx) => (
                              <span
                                key={idx}
                                className={`text-xs px-2 py-1 rounded ${
                                  p.relevance === 'primary'
                                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                    : 'bg-slate-800 text-slate-400'
                                }`}
                              >
                                {p.law_name} {p.article}
                                {p.relevance === 'primary' && <span className="ml-1 text-emerald-300">主</span>}
                              </span>
                            ))}
                          </div>

                          {/* Common Elements Preview */}
                          <div className="flex flex-wrap gap-1.5">
                            {violation.common_elements.slice(0, 3).map((element, idx) => (
                              <span key={idx} className="badge badge-violet text-xs">{element}</span>
                            ))}
                            {violation.common_elements.length > 3 && (
                              <span className="badge badge-slate text-xs">+{violation.common_elements.length - 3}</span>
                            )}
                          </div>
                        </div>

                        <svg className="w-5 h-5 text-slate-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Legal Provisions with Elements */}
            <div>
              <h3 className="text-xl font-serif font-semibold text-slate-100 mb-4">法條與構成要件詳解</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {MOCK_PROVISIONS
                  .filter(p => !searchQuery.trim() ||
                    p.law_name.includes(searchQuery) ||
                    p.article.includes(searchQuery) ||
                    p.constitutive_elements.some(e => e.element_name.includes(searchQuery))
                  )
                  .map((provision) => (
                  <div
                    key={provision.id}
                    className="card p-5 hover:border-emerald-500/30 transition-all cursor-pointer"
                    onClick={() => setSelectedProvision(provision)}
                  >
                    <div className="flex items-start gap-3 mb-4">
                      <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                        <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-base font-medium text-slate-100">{provision.law_name}</h4>
                        <p className="text-sm text-emerald-400">{provision.article}</p>
                      </div>
                      <span className="badge badge-slate text-xs">{provision.constitutive_elements.length} 要件</span>
                    </div>

                    {/* Constitutive Elements Preview */}
                    <div className="space-y-2 mb-3">
                      {provision.constitutive_elements.slice(0, 3).map((element) => (
                        <div key={element.id} className="flex items-center gap-2 text-sm">
                          {element.required ? (
                            <span className="w-5 h-5 rounded bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                              <svg className="w-3 h-3 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </span>
                          ) : (
                            <span className="w-5 h-5 rounded bg-slate-800 flex items-center justify-center flex-shrink-0">
                              <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                            </span>
                          )}
                          <span className={element.required ? 'text-slate-200' : 'text-slate-400'}>
                            {element.element_name}
                          </span>
                          {element.required && (
                            <span className="text-xs text-amber-400/70">必要</span>
                          )}
                        </div>
                      ))}
                      {provision.constitutive_elements.length > 3 && (
                        <p className="text-xs text-slate-500 pl-7">
                          還有 {provision.constitutive_elements.length - 3} 項要件...
                        </p>
                      )}
                    </div>

                    {provision.penalty_range && (
                      <div className="pt-3 border-t border-slate-800/50">
                        <p className="text-xs text-slate-500">
                          <span className="text-slate-400">罰則：</span> {provision.penalty_range}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Document Detail Modal with Legal Basis */}
      {selectedDocument && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="card w-full max-w-3xl max-h-[85vh] overflow-hidden">
            <div className="p-5 border-b border-slate-800/50 flex items-center justify-between">
              <h3 className="text-lg font-serif font-semibold text-slate-100">案件詳情</h3>
              <button
                onClick={() => setSelectedDocument(null)}
                className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">
              <h4 className="text-lg font-medium text-slate-100 mb-4">{selectedDocument.filename}</h4>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="meta-item">
                  <span className="meta-label">裁罰日期</span>
                  <span className="meta-value">{formatDate(selectedDocument.date)}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">監理機關</span>
                  <span className="meta-value">{selectedDocument.issuing_authority || '-'}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">受罰機構</span>
                  <span className="meta-value">{selectedDocument.related_institutions?.join(', ') || '-'}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">違規類型</span>
                  <span className="meta-value">{selectedDocument.violation_types?.join(', ') || '-'}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">文件類型</span>
                  <span className="meta-value">{selectedDocument.document_type || '-'}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">提取信心度</span>
                  <span className="meta-value">
                    {selectedDocument.extraction_confidence !== null
                      ? `${(selectedDocument.extraction_confidence * 100).toFixed(0)}%`
                      : '-'}
                  </span>
                </div>
              </div>

              {/* Legal Basis Section - 構成要件 */}
              {selectedDocument.violation_types && selectedDocument.violation_types.length > 0 && (
                <div className="mb-6">
                  <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                    法律依據與構成要件
                  </h5>
                  <div className="space-y-3">
                    {selectedDocument.violation_types.map((vt) => {
                      // Find matching violation legal basis
                      const basis = VIOLATION_LEGAL_BASIS.find(b =>
                        b.violation_type === vt ||
                        b.violation_type.includes(vt) ||
                        vt.includes(b.violation_type.replace('缺失', '').replace('違規', ''))
                      );

                      if (!basis) return null;

                      return (
                        <div
                          key={vt}
                          className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/50 hover:border-violet-500/30 transition-colors cursor-pointer"
                          onClick={() => {
                            setSelectedDocument(null);
                            setSelectedViolationBasis(basis);
                          }}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <span className="badge badge-rose">{vt}</span>
                            <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </div>

                          {/* Primary Legal Provisions */}
                          <div className="flex flex-wrap gap-2 mb-3">
                            {basis.provisions.map((p, idx) => (
                              <span
                                key={idx}
                                className={`text-xs px-2 py-1 rounded ${
                                  p.relevance === 'primary'
                                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                    : 'bg-slate-800 text-slate-400'
                                }`}
                              >
                                {p.law_name} {p.article}
                              </span>
                            ))}
                          </div>

                          {/* Constitutive Elements */}
                          <div className="flex flex-wrap gap-1.5">
                            {basis.common_elements.map((element, idx) => (
                              <span key={idx} className="text-xs px-2 py-0.5 rounded bg-violet-500/10 text-violet-300">
                                {element}
                              </span>
                            ))}
                          </div>

                          {/* Typical Penalties */}
                          <div className="mt-3 pt-3 border-t border-slate-700/30">
                            <p className="text-xs text-slate-500">
                              <span className="text-slate-400">常見處分：</span>
                              {basis.typical_penalties.slice(0, 2).join('、')}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <a href="/" className="btn btn-primary flex-1" onClick={() => setSelectedDocument(null)}>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  相關研究
                </a>
                <button
                  onClick={() => {
                    setSelectedDocument(null);
                    setViewMode('elements');
                  }}
                  className="btn btn-secondary"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  構成要件
                </button>
                <button onClick={() => setSelectedDocument(null)} className="btn btn-secondary">
                  關閉
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Legal Provision Modal with Constitutive Elements */}
      {selectedProvision && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="card w-full max-w-3xl max-h-[85vh] overflow-hidden">
            <div className="p-5 border-b border-slate-800/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-serif font-semibold text-slate-100">{selectedProvision.law_name}</h3>
                  <p className="text-sm text-emerald-400">{selectedProvision.article}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedProvision(null)}
                className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">
              {/* Category and Authority */}
              <div className="flex items-center gap-3 mb-4">
                <span className="badge badge-emerald">{selectedProvision.category}</span>
                <span className="text-xs text-slate-500">主管機關：{selectedProvision.authority}</span>
              </div>

              {/* Law Content */}
              <div className="mb-6 p-4 bg-slate-800/30 rounded-lg border border-slate-700/50">
                <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-2">條文內容</h5>
                <p className="text-slate-300 leading-relaxed text-sm">{selectedProvision.content}</p>
              </div>

              {/* Constitutive Elements - 構成要件 */}
              <div className="mb-6">
                <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  構成要件分析
                </h5>
                <div className="space-y-3">
                  {selectedProvision.constitutive_elements.map((element, idx) => (
                    <div
                      key={element.id}
                      className={`p-4 rounded-lg border ${
                        element.required
                          ? 'bg-amber-500/5 border-amber-500/20'
                          : 'bg-slate-800/30 border-slate-700/50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 ${
                          element.required
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-slate-700 text-slate-400'
                        }`}>
                          {idx + 1}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`font-medium ${element.required ? 'text-amber-200' : 'text-slate-200'}`}>
                              {element.element_name}
                            </span>
                            {element.required && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                必要要件
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-400">{element.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Penalty Range */}
              {selectedProvision.penalty_range && (
                <div className="mb-6 p-4 bg-rose-500/5 rounded-lg border border-rose-500/20">
                  <h5 className="text-sm font-medium text-rose-400 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    罰則範圍
                  </h5>
                  <p className="text-sm text-slate-300">{selectedProvision.penalty_range}</p>
                </div>
              )}

              {/* Related Violations */}
              <div className="mb-6">
                <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">相關違規類型</h5>
                <div className="flex flex-wrap gap-2">
                  {selectedProvision.related_violations.map((v, i) => (
                    <span key={i} className="badge badge-rose">{v}</span>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setSelectedProvision(null);
                    setViewMode('cases');
                    setSearchQuery(selectedProvision.related_violations[0] || '');
                  }}
                  className="btn btn-primary flex-1"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  查看相關案例
                </button>
                <button onClick={() => setSelectedProvision(null)} className="btn btn-secondary">
                  關閉
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Concept Detail Modal */}
      {selectedConcept && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="card w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="p-5 border-b border-slate-800/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg bg-${selectedConcept.color}-500/10 flex items-center justify-center`}>
                  <ConceptIcon name={selectedConcept.icon} className={`w-5 h-5 text-${selectedConcept.color}-400`} />
                </div>
                <h3 className="text-lg font-serif font-semibold text-slate-100">{selectedConcept.title}</h3>
              </div>
              <button
                onClick={() => setSelectedConcept(null)}
                className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto">
              <p className="text-slate-300 leading-relaxed mb-6">{selectedConcept.description}</p>

              <div className="mb-6 p-4 bg-slate-800/30 rounded-lg">
                <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-2">學習重點</h5>
                <ul className="text-sm text-slate-300 space-y-2">
                  <li className="flex items-start gap-2">
                    <svg className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    了解相關法規的核心要求與規範重點
                  </li>
                  <li className="flex items-start gap-2">
                    <svg className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    從實際案例中學習常見的違規態樣
                  </li>
                  <li className="flex items-start gap-2">
                    <svg className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    掌握監理機關的裁罰標準與處分原則
                  </li>
                </ul>
              </div>

              <div className="flex items-center justify-between mb-6 p-4 bg-slate-800/30 rounded-lg">
                <div>
                  <p className="text-sm text-slate-400">相關案例數量</p>
                  <p className="text-2xl font-mono font-semibold text-slate-100">{selectedConcept.relatedCount}</p>
                </div>
                <div className={`w-12 h-12 rounded-full bg-${selectedConcept.color}-500/20 flex items-center justify-center`}>
                  <ConceptIcon name={selectedConcept.icon} className={`w-6 h-6 text-${selectedConcept.color}-400`} />
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setSelectedConcept(null);
                    setViewMode('cases');
                    setSearchQuery(selectedConcept.title);
                  }}
                  className="btn btn-primary flex-1"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  瀏覽相關案例
                </button>
                <button
                  onClick={() => {
                    setSelectedConcept(null);
                    setViewMode('laws');
                  }}
                  className="btn btn-secondary"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  相關法規
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Violation Legal Basis Modal - 違規類型與構成要件 */}
      {selectedViolationBasis && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="card w-full max-w-3xl max-h-[85vh] overflow-hidden">
            <div className="p-5 border-b border-slate-800/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-serif font-semibold text-slate-100">{selectedViolationBasis.violation_type}</h3>
                  <p className="text-sm text-slate-400">違規類型構成要件分析</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedViolationBasis(null)}
                className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">
              {/* Legal Provisions */}
              <div className="mb-6">
                <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  法律依據
                </h5>
                <div className="space-y-3">
                  {selectedViolationBasis.provisions.map((provision, idx) => {
                    const fullProvision = MOCK_PROVISIONS.find(p => p.id === provision.provision_id);
                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-lg border cursor-pointer transition-all hover:border-emerald-500/40 ${
                          provision.relevance === 'primary'
                            ? 'bg-emerald-500/5 border-emerald-500/20'
                            : 'bg-slate-800/30 border-slate-700/50'
                        }`}
                        onClick={() => {
                          if (fullProvision) {
                            setSelectedViolationBasis(null);
                            setSelectedProvision(fullProvision);
                          }
                        }}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`font-medium ${provision.relevance === 'primary' ? 'text-emerald-300' : 'text-slate-200'}`}>
                              {provision.law_name}
                            </span>
                            <span className="text-emerald-400 text-sm">{provision.article}</span>
                          </div>
                          {provision.relevance === 'primary' && (
                            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              主要法源
                            </span>
                          )}
                        </div>
                        {fullProvision && (
                          <p className="text-sm text-slate-400 line-clamp-2">{fullProvision.content}</p>
                        )}
                        <div className="flex items-center gap-1 mt-2 text-xs text-slate-500">
                          <span>點擊查看完整條文與構成要件</span>
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Common Constitutive Elements */}
              <div className="mb-6">
                <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  常見構成要件
                </h5>
                <div className="p-4 bg-violet-500/5 rounded-lg border border-violet-500/20">
                  <div className="space-y-3">
                    {selectedViolationBasis.common_elements.map((element, idx) => (
                      <div key={idx} className="flex items-start gap-3">
                        <span className="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center text-xs font-medium text-violet-300 flex-shrink-0">
                          {idx + 1}
                        </span>
                        <span className="text-slate-200">{element}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <p className="mt-3 text-xs text-slate-500">
                  符合上述構成要件者，可能構成此類違規行為，主管機關得依法裁處。
                </p>
              </div>

              {/* Typical Penalties */}
              <div className="mb-6">
                <h5 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  常見處分類型
                </h5>
                <div className="flex flex-wrap gap-2">
                  {selectedViolationBasis.typical_penalties.map((penalty, idx) => (
                    <span key={idx} className="px-3 py-1.5 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20 text-sm">
                      {penalty}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setSelectedViolationBasis(null);
                    setViewMode('cases');
                    setSearchQuery(selectedViolationBasis.violation_type);
                  }}
                  className="btn btn-primary flex-1"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  搜尋相關案例
                </button>
                <button onClick={() => setSelectedViolationBasis(null)} className="btn btn-secondary">
                  關閉
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
