/**
 * SettingsPage v2.0 - System Configuration Management
 *
 * Tabs:
 * - Models: LLM and Embedding model configuration
 * - Documents: Document management and indexing
 * - System: General settings and presets
 */

import { useState, useEffect, useCallback } from 'react';

// ============================================
// Types
// ============================================

interface LLMModel {
  id: string;
  name: string;
  description: string;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  max_tokens: number;
  recommended: boolean;
  is_active: boolean;
}

interface EmbeddingModel {
  id: string;
  name: string;
  description: string;
  dimensions: number;
  cost_per_1k_tokens: number;
  recommended: boolean;
  is_active: boolean;
}

interface ActiveLLM {
  model: string;
  api_key: string;
  base_url: string;
  temperature: number;
}

interface ConnectionTestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
  model: string | null;
}

interface Preset {
  id: number;
  name: string;
  config_type: string;
  model: string;
  api_key: string;
  base_url: string;
  temperature: number | null;
  is_active: boolean;
  created_at: string;
}

interface DocumentInfo {
  id: string;
  name: string;
  file_path: string;
  size_bytes: number;
  status: string;  // pending, indexed, error
  chunk_count: number;
  version: number;
  created_at: string;
  updated_at: string;
  description: string | null;
  document_type: string | null;

  // Pipeline monitoring fields
  pipeline_stage: string | null;
  pipeline_status: string | null;

  // Metadata extraction status
  indexed: boolean;
  metadata_extracted: boolean;
  metadata_extraction_status: string;  // pending, processing, completed, failed, user_edited
  extraction_confidence: number | null;

  // Additional metadata
  issuing_authority: string | null;
  related_institutions: string[] | null;
  violation_types: string[] | null;
  penalty_amount: string | null;
  keywords: string[] | null;
}

interface IndexStatus {
  total_documents: number;
  indexed_documents: number;
  pending_documents: number;
  error_documents: number;
  total_chunks: number;
  last_indexed_at: string | null;
}

interface DirectoryInfo {
  name: string;
  path: string;
  file_count: number;
  total_size_bytes: number;
  subdirectories: DirectoryInfo[];
}

interface DirectoryStructure {
  base_path: string;
  directories: DirectoryInfo[];
  total_files: number;
  total_size_bytes: number;
}

interface ScanResult {
  total_files_found: number;
  new_files: number;
  existing_files: number;
  indexed_files: number;
  failed_files: number;
  directories_scanned: number;
  new_file_list: string[];
  directory_structure: DirectoryInfo[];
  message: string;
}

interface UsageStats {
  total_tokens: number;
  total_cost: number;
  queries_count: number;
  session_start: string;
  current_llm_model: string;
  current_embedding_model: string;
}

// ============================================
// Default System Prompts
// ============================================

const DEFAULT_QUERY_ANALYZER_PROMPT = `You are a query analysis expert specializing in financial legal research.
Your task is to analyze the user's query and provide insights about:
1. Query type (factual, analytical, comparative, temporal, etc.)
2. Key entities (bank names, dates, amounts, regulations, legal concepts)
3. Recommended search strategy (semantic, keyword, or hybrid)
4. Query complexity (simple, medium, complex)
5. Brief reasoning for your analysis

Search Strategy Guidelines:
- semantic: Pure conceptual/analytical queries without specific terms
- keyword: Queries requiring exact matches of ALL specified terms
- hybrid: Queries with BOTH specific terms (dates, amounts, names) AND concepts (recommended for most queries)`;

const DEFAULT_REPORTER_PROMPT = `You are a professional financial legal researcher.
Your task is to compile a final report based on the executed research plan and results.

Instructions:
1. Synthesize the information into a clear, structured report.
2. Use the following structure:
   - **Executive Summary**: A brief overview of the findings.
   - **Key Findings**: Detailed points with evidence.
   - **Analysis**: Connection to relevant laws and regulations.
   - **Conclusion**: Final answer to the user's query.
3. Cite your sources explicitly using the [Source Name] format.
4. If the results are insufficient, state what is missing.
5. Use Traditional Chinese (繁體中文).`;

// ============================================
// API Functions
// ============================================

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Models API
async function fetchLLMModels(): Promise<LLMModel[]> {
  const res = await fetch(`${API_BASE}/api/v1/models/llm/available`);
  if (!res.ok) throw new Error('Failed to fetch LLM models');
  return res.json();
}

async function fetchEmbeddingModels(): Promise<EmbeddingModel[]> {
  const res = await fetch(`${API_BASE}/api/v1/models/embedding/available`);
  if (!res.ok) throw new Error('Failed to fetch embedding models');
  return res.json();
}

async function fetchActiveLLM(): Promise<ActiveLLM> {
  const res = await fetch(`${API_BASE}/api/v1/models/llm/active`);
  if (!res.ok) throw new Error('Failed to fetch active LLM');
  return res.json();
}

async function setActiveLLM(modelId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/models/llm/active`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId }),
  });
  if (!res.ok) throw new Error('Failed to set LLM model');
}

async function setActiveEmbedding(modelId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/models/embedding/active`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId }),
  });
  if (!res.ok) throw new Error('Failed to set embedding model');
}

async function testLLMConnection(): Promise<ConnectionTestResult> {
  const res = await fetch(`${API_BASE}/api/v1/models/llm/test`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to test connection');
  return res.json();
}

async function fetchUsageStats(): Promise<UsageStats> {
  const res = await fetch(`${API_BASE}/api/v1/models/stats`);
  if (!res.ok) throw new Error('Failed to fetch usage stats');
  return res.json();
}

// Config API
async function fetchPresets(configType?: string): Promise<Preset[]> {
  const url = configType
    ? `${API_BASE}/api/v1/config/presets?config_type=${configType}`
    : `${API_BASE}/api/v1/config/presets`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch presets');
  return res.json();
}

async function activatePreset(presetId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/config/presets/${presetId}/activate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to activate preset');
}

async function deletePreset(presetId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/config/presets/${presetId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete preset');
}

async function createPreset(preset: {
  name: string;
  config_type: string;
  model: string;
  api_key?: string;
  base_url?: string;
  temperature?: number;
  set_active?: boolean;
}): Promise<Preset> {
  const res = await fetch(`${API_BASE}/api/v1/config/presets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preset),
  });
  if (!res.ok) throw new Error('Failed to create preset');
  return res.json();
}

async function updateSetting(key: string, value: string, category?: string): Promise<void> {
  // Use POST for upsert (create or update)
  const res = await fetch(`${API_BASE}/api/v1/config/settings/${key}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value, category: category || 'prompts' }),
  });
  if (!res.ok) throw new Error('Failed to update setting');
}

// Documents API
async function fetchDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/api/v1/documents/`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

async function fetchIndexStatus(): Promise<IndexStatus> {
  const res = await fetch(`${API_BASE}/api/v1/documents/status`);
  if (!res.ok) throw new Error('Failed to fetch index status');
  return res.json();
}

async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
}

async function triggerReindex(extractMetadata: boolean = false): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/documents/reindex-all`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ extract_metadata: extractMetadata }),
  });
  if (!res.ok) throw new Error('Failed to trigger reindex');
}

async function fetchDirectoryStructure(): Promise<DirectoryStructure> {
  const res = await fetch(`${API_BASE}/api/v1/documents/directory-structure`);
  if (!res.ok) throw new Error('Failed to fetch directory structure');
  return res.json();
}

async function scanDirectory(extractMetadata: boolean = false, indexNew: boolean = true): Promise<ScanResult> {
  const res = await fetch(`${API_BASE}/api/v1/documents/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ extract_metadata: extractMetadata, index_new: indexNew }),
  });
  if (!res.ok) throw new Error('Failed to scan directory');
  return res.json();
}

async function scanPreview(): Promise<ScanResult> {
  const res = await fetch(`${API_BASE}/api/v1/documents/scan-preview`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to preview scan');
  return res.json();
}

// System Prompts API
async function fetchSetting(key: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/config/settings`);
  if (!res.ok) throw new Error('Failed to fetch settings');
  const data = await res.json();
  // Search through all categories
  for (const category of Object.values(data) as Array<Array<{ key: string; value: string }>>) {
    const setting = category.find((s) => s.key === key);
    if (setting) return setting.value;
  }
  return '';
}

// ============================================
// Main Component
// ============================================

type SettingsTab = 'models' | 'documents' | 'system';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('models');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Models state
  const [llmModels, setLLMModels] = useState<LLMModel[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<EmbeddingModel[]>([]);
  const [activeLLM, setActiveLLMState] = useState<ActiveLLM | null>(null);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);

  // Documents state
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [directoryStructure, setDirectoryStructure] = useState<DirectoryStructure | null>(null);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [scanning, setScanning] = useState(false);

  // Presets state
  const [presets, setPresets] = useState<Preset[]>([]);
  const [showCreatePreset, setShowCreatePreset] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');

  // Model configuration editing - LLM
  const [editingApiKey, setEditingApiKey] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
  const [editingLLMModel, setEditingLLMModel] = useState(false);
  const [editingBaseUrl, setEditingBaseUrl] = useState(false);
  const [editingTemperature, setEditingTemperature] = useState(false);
  const [newLLMModel, setNewLLMModel] = useState('');
  const [newBaseUrl, setNewBaseUrl] = useState('');
  const [newTemperature, setNewTemperature] = useState('');

  // Model configuration editing - Embedding
  const [editingEmbeddingModel, setEditingEmbeddingModel] = useState(false);
  const [editingEmbeddingApiKey, setEditingEmbeddingApiKey] = useState(false);
  const [editingEmbeddingBaseUrl, setEditingEmbeddingBaseUrl] = useState(false);
  const [newEmbeddingModel, setNewEmbeddingModel] = useState('');
  const [newEmbeddingApiKey, setNewEmbeddingApiKey] = useState('');
  const [newEmbeddingBaseUrl, setNewEmbeddingBaseUrl] = useState('');

  // System Prompt editing
  const [queryAnalyzerPrompt, setQueryAnalyzerPrompt] = useState('');
  const [reporterPrompt, setReporterPrompt] = useState('');
  const [editingQueryAnalyzerPrompt, setEditingQueryAnalyzerPrompt] = useState(false);
  const [editingReporterPrompt, setEditingReporterPrompt] = useState(false);
  const [newQueryAnalyzerPrompt, setNewQueryAnalyzerPrompt] = useState('');
  const [newReporterPrompt, setNewReporterPrompt] = useState('');

  // Load data based on active tab
  useEffect(() => {
    if (activeTab === 'models') {
      loadModelsData();
    } else if (activeTab === 'documents') {
      loadDocumentsData();
    } else if (activeTab === 'system') {
      loadPresetsData();
    }
  }, [activeTab]);

  const loadModelsData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [llm, embedding, active, stats] = await Promise.all([
        fetchLLMModels(),
        fetchEmbeddingModels(),
        fetchActiveLLM(),
        fetchUsageStats(),
      ]);
      setLLMModels(llm);
      setEmbeddingModels(embedding);
      setActiveLLMState(active);
      setUsageStats(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentsData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [docs, status, dirStructure] = await Promise.all([
        fetchDocuments(),
        fetchIndexStatus(),
        fetchDirectoryStructure(),
      ]);
      setDocuments(docs);
      setIndexStatus(status);
      setDirectoryStructure(dirStructure);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const loadPresetsData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [data, queryPrompt, reportPrompt] = await Promise.all([
        fetchPresets(),
        fetchSetting('query_analyzer_prompt'),
        fetchSetting('reporter_prompt'),
      ]);
      setPresets(data);
      setQueryAnalyzerPrompt(queryPrompt);
      setReporterPrompt(reportPrompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load presets');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectLLM = async (modelId: string) => {
    try {
      setLoading(true);
      await setActiveLLM(modelId);
      setSuccess(`已切換到 ${modelId}`);
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set LLM');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEmbedding = async (modelId: string) => {
    try {
      setLoading(true);
      await setActiveEmbedding(modelId);
      setSuccess(`Embedding 模型已切換到 ${modelId}`);
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set embedding');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const result = await testLLMConnection();
      setTestResult(result);
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'Test failed',
        latency_ms: null,
        model: null,
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!newApiKey.trim()) return;
    try {
      setLoading(true);
      await updateSetting('llm_api_key', newApiKey);
      setSuccess('API Key 已更新');
      setEditingApiKey(false);
      setNewApiKey('');
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm('確定要刪除此文件嗎？')) return;
    try {
      setLoading(true);
      await deleteDocument(docId);
      setSuccess('文件已刪除');
      await loadDocumentsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async (extractMetadata: boolean = false) => {
    try {
      setReindexing(true);
      await triggerReindex(extractMetadata);
      setSuccess('重新索引已開始');
      // Poll for completion
      setTimeout(() => loadDocumentsData(), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger reindex');
    } finally {
      setReindexing(false);
    }
  };

  const handleScanPreview = async () => {
    try {
      setScanning(true);
      setScanResult(null);
      const result = await scanPreview();
      setScanResult(result);
      if (result.new_files > 0) {
        setSuccess(`發現 ${result.new_files} 個新檔案`);
      } else {
        setSuccess('目錄已同步，無新檔案');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scan directory');
    } finally {
      setScanning(false);
    }
  };

  const handleScanAndIndex = async (extractMetadata: boolean = false) => {
    try {
      setScanning(true);
      setScanResult(null);
      const result = await scanDirectory(extractMetadata, true);
      setScanResult(result);
      if (result.indexed_files > 0) {
        setSuccess(`成功索引 ${result.indexed_files} 個檔案`);
        await loadDocumentsData(); // Refresh documents list
      } else if (result.new_files === 0) {
        setSuccess('目錄已同步，無新檔案');
      } else {
        setError(`索引失敗：${result.failed_files} 個檔案`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scan and index');
    } finally {
      setScanning(false);
    }
  };

  const handleActivatePreset = async (presetId: number) => {
    try {
      setLoading(true);
      await activatePreset(presetId);
      setSuccess('預設已啟用');
      await loadPresetsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to activate preset');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePreset = async (presetId: number) => {
    if (!confirm('確定要刪除此預設嗎？')) return;
    try {
      setLoading(true);
      await deletePreset(presetId);
      setSuccess('預設已刪除');
      await loadPresetsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete preset');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePreset = async () => {
    if (!newPresetName.trim() || !activeLLM) return;
    try {
      setLoading(true);
      await createPreset({
        name: newPresetName,
        config_type: 'llm',
        model: activeLLM.model,
        set_active: false,
      });
      setSuccess('預設已建立');
      setShowCreatePreset(false);
      setNewPresetName('');
      await loadPresetsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create preset');
    } finally {
      setLoading(false);
    }
  };

  // Clear notifications after 3 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // ============================================
  // Model Configuration Handlers
  // ============================================

  const handleSaveLLMModel = async () => {
    if (!newLLMModel.trim()) return;
    try {
      setLoading(true);
      await updateSetting('llm_model', newLLMModel);
      setSuccess('LLM 模型已更新');
      setEditingLLMModel(false);
      setNewLLMModel('');
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save LLM model');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEmbeddingModel = async () => {
    if (!newEmbeddingModel.trim()) return;
    try {
      setLoading(true);
      await updateSetting('embedding_model', newEmbeddingModel);
      setSuccess('Embedding 模型已更新');
      setEditingEmbeddingModel(false);
      setNewEmbeddingModel('');
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save embedding model');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEmbeddingApiKey = async () => {
    if (!newEmbeddingApiKey.trim()) return;
    try {
      setLoading(true);
      await updateSetting('embedding_api_key', newEmbeddingApiKey);
      setSuccess('Embedding API Key 已更新');
      setEditingEmbeddingApiKey(false);
      setNewEmbeddingApiKey('');
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save embedding API key');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEmbeddingBaseUrl = async () => {
    try {
      setLoading(true);
      await updateSetting('embedding_base_url', newEmbeddingBaseUrl);
      setSuccess('Embedding Base URL 已更新');
      setEditingEmbeddingBaseUrl(false);
      setNewEmbeddingBaseUrl('');
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save embedding base URL');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveBaseUrl = async () => {
    try {
      setLoading(true);
      await updateSetting('llm_base_url', newBaseUrl);
      setSuccess('Base URL 已更新');
      setEditingBaseUrl(false);
      setNewBaseUrl('');
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save base URL');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTemperature = async () => {
    const temp = parseFloat(newTemperature);
    if (isNaN(temp) || temp < 0 || temp > 2) {
      setError('Temperature 必須在 0-2 之間');
      return;
    }
    try {
      setLoading(true);
      await updateSetting('llm_temperature', newTemperature);
      setSuccess('Temperature 已更新');
      setEditingTemperature(false);
      setNewTemperature('');
      await loadModelsData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save temperature');
    } finally {
      setLoading(false);
    }
  };

  // System Prompt Handlers
  const handleSaveQueryAnalyzerPrompt = async () => {
    try {
      setLoading(true);
      await updateSetting('query_analyzer_prompt', newQueryAnalyzerPrompt, 'prompts');
      setSuccess('問題理解提示詞已更新');
      setEditingQueryAnalyzerPrompt(false);
      setQueryAnalyzerPrompt(newQueryAnalyzerPrompt);
      setNewQueryAnalyzerPrompt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save query analyzer prompt');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveReporterPrompt = async () => {
    try {
      setLoading(true);
      await updateSetting('reporter_prompt', newReporterPrompt, 'prompts');
      setSuccess('報告生成提示詞已更新');
      setEditingReporterPrompt(false);
      setReporterPrompt(newReporterPrompt);
      setNewReporterPrompt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save reporter prompt');
    } finally {
      setLoading(false);
    }
  };

  const renderModelsTab = () => (
    <div className="space-y-6">
      {/* LLM Configuration */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-noir-100 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
          LLM 設定
        </h3>

        {activeLLM && (
          <div className="space-y-4">
            {/* LLM Model */}
            <div className="bg-noir-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-noir-500 mb-1">模型名稱</div>
                {!editingLLMModel && (
                  <button
                    onClick={() => { setEditingLLMModel(true); setNewLLMModel(activeLLM.model); }}
                    className="text-xs text-brass-400 hover:text-brass-300"
                  >
                    編輯
                  </button>
                )}
              </div>
              {editingLLMModel ? (
                <div className="flex items-center gap-2 mt-2">
                  <input
                    type="text"
                    value={newLLMModel}
                    onChange={(e) => setNewLLMModel(e.target.value)}
                    placeholder="例如: gpt-4o-mini, gpt-4o, claude-3-5-sonnet..."
                    className="flex-1 bg-noir-700 border border-noir-600 rounded px-3 py-2 text-sm text-noir-200"
                  />
                  <button onClick={handleSaveLLMModel} className="btn btn-primary text-sm">儲存</button>
                  <button
                    onClick={() => { setEditingLLMModel(false); setNewLLMModel(''); }}
                    className="btn btn-secondary text-sm"
                  >
                    取消
                  </button>
                </div>
              ) : (
                <div className="text-sm text-brass-400 font-medium">{activeLLM.model}</div>
              )}
            </div>

            {/* API Key */}
            <div className="bg-noir-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-noir-500 mb-1">API Key</div>
                {!editingApiKey && (
                  <button
                    onClick={() => setEditingApiKey(true)}
                    className="text-xs text-brass-400 hover:text-brass-300"
                  >
                    編輯
                  </button>
                )}
              </div>
              {editingApiKey ? (
                <div className="flex items-center gap-2 mt-2">
                  <input
                    type="password"
                    value={newApiKey}
                    onChange={(e) => setNewApiKey(e.target.value)}
                    placeholder="輸入新的 API Key..."
                    className="flex-1 bg-noir-700 border border-noir-600 rounded px-3 py-2 text-sm text-noir-200"
                  />
                  <button onClick={handleSaveApiKey} className="btn btn-primary text-sm">儲存</button>
                  <button
                    onClick={() => { setEditingApiKey(false); setNewApiKey(''); }}
                    className="btn btn-secondary text-sm"
                  >
                    取消
                  </button>
                </div>
              ) : (
                <div className="text-sm text-noir-300 font-mono">{activeLLM.api_key || '未設定'}</div>
              )}
            </div>

            {/* Base URL */}
            <div className="bg-noir-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-noir-500 mb-1">Base URL</div>
                {!editingBaseUrl && (
                  <button
                    onClick={() => { setEditingBaseUrl(true); setNewBaseUrl(activeLLM.base_url || ''); }}
                    className="text-xs text-brass-400 hover:text-brass-300"
                  >
                    編輯
                  </button>
                )}
              </div>
              {editingBaseUrl ? (
                <div className="flex items-center gap-2 mt-2">
                  <input
                    type="text"
                    value={newBaseUrl}
                    onChange={(e) => setNewBaseUrl(e.target.value)}
                    placeholder="留空使用 OpenAI 預設，或輸入自訂 URL..."
                    className="flex-1 bg-noir-700 border border-noir-600 rounded px-3 py-2 text-sm text-noir-200"
                  />
                  <button onClick={handleSaveBaseUrl} className="btn btn-primary text-sm">儲存</button>
                  <button
                    onClick={() => { setEditingBaseUrl(false); setNewBaseUrl(''); }}
                    className="btn btn-secondary text-sm"
                  >
                    取消
                  </button>
                </div>
              ) : (
                <div className="text-sm text-noir-300">{activeLLM.base_url || 'OpenAI (預設)'}</div>
              )}
            </div>

            {/* Temperature */}
            <div className="bg-noir-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-noir-500 mb-1">Temperature</div>
                {!editingTemperature && (
                  <button
                    onClick={() => { setEditingTemperature(true); setNewTemperature(String(activeLLM.temperature)); }}
                    className="text-xs text-brass-400 hover:text-brass-300"
                  >
                    編輯
                  </button>
                )}
              </div>
              {editingTemperature ? (
                <div className="flex items-center gap-2 mt-2">
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={newTemperature}
                    onChange={(e) => setNewTemperature(e.target.value)}
                    placeholder="0.0 - 2.0"
                    className="w-24 bg-noir-700 border border-noir-600 rounded px-3 py-2 text-sm text-noir-200"
                  />
                  <span className="text-xs text-noir-500">（0 = 確定性，1 = 平衡，2 = 創意）</span>
                  <button onClick={handleSaveTemperature} className="btn btn-primary text-sm">儲存</button>
                  <button
                    onClick={() => { setEditingTemperature(false); setNewTemperature(''); }}
                    className="btn btn-secondary text-sm"
                  >
                    取消
                  </button>
                </div>
              ) : (
                <div className="text-sm text-noir-200">{activeLLM.temperature}</div>
              )}
            </div>
          </div>
        )}

        {/* Test Connection Button */}
        <div className="mt-6 flex items-center gap-4">
          <button
            onClick={handleTestConnection}
            disabled={testing}
            className="btn btn-secondary"
          >
            {testing ? (
              <>
                <div className="w-4 h-4 border-2 border-brass-500 border-t-transparent rounded-full animate-spin mr-2" />
                測試中...
              </>
            ) : (
              '測試 LLM 連線'
            )}
          </button>

          {testResult && (
            <div className={`text-sm ${testResult.success ? 'text-jade-400' : 'text-vermilion-400'}`}>
              {testResult.message}
              {testResult.latency_ms && ` (${testResult.latency_ms.toFixed(0)}ms)`}
            </div>
          )}
        </div>
      </div>

      {/* Embedding Configuration */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-noir-100 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
          </svg>
          Embedding 設定
        </h3>

        <div className="space-y-4">
          {/* Embedding Model */}
          <div className="bg-noir-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-noir-500 mb-1">模型名稱</div>
              {!editingEmbeddingModel && (
                <button
                  onClick={() => { setEditingEmbeddingModel(true); setNewEmbeddingModel(usageStats?.current_embedding_model || ''); }}
                  className="text-xs text-brass-400 hover:text-brass-300"
                >
                  編輯
                </button>
              )}
            </div>
            {editingEmbeddingModel ? (
              <div className="flex items-center gap-2 mt-2">
                <input
                  type="text"
                  value={newEmbeddingModel}
                  onChange={(e) => setNewEmbeddingModel(e.target.value)}
                  placeholder="例如: text-embedding-3-small, text-embedding-3-large..."
                  className="flex-1 bg-noir-700 border border-noir-600 rounded px-3 py-2 text-sm text-noir-200"
                />
                <button onClick={handleSaveEmbeddingModel} className="btn btn-primary text-sm">儲存</button>
                <button
                  onClick={() => { setEditingEmbeddingModel(false); setNewEmbeddingModel(''); }}
                  className="btn btn-secondary text-sm"
                >
                  取消
                </button>
              </div>
            ) : (
              <div className="text-sm text-brass-400 font-medium">
                {usageStats?.current_embedding_model || '未設定'}
              </div>
            )}
          </div>

          {/* Embedding API Key */}
          <div className="bg-noir-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-noir-500 mb-1">API Key</div>
              {!editingEmbeddingApiKey && (
                <button
                  onClick={() => setEditingEmbeddingApiKey(true)}
                  className="text-xs text-brass-400 hover:text-brass-300"
                >
                  編輯
                </button>
              )}
            </div>
            {editingEmbeddingApiKey ? (
              <div className="flex items-center gap-2 mt-2">
                <input
                  type="password"
                  value={newEmbeddingApiKey}
                  onChange={(e) => setNewEmbeddingApiKey(e.target.value)}
                  placeholder="輸入 Embedding API Key（留空使用 LLM API Key）..."
                  className="flex-1 bg-noir-700 border border-noir-600 rounded px-3 py-2 text-sm text-noir-200"
                />
                <button onClick={handleSaveEmbeddingApiKey} className="btn btn-primary text-sm">儲存</button>
                <button
                  onClick={() => { setEditingEmbeddingApiKey(false); setNewEmbeddingApiKey(''); }}
                  className="btn btn-secondary text-sm"
                >
                  取消
                </button>
              </div>
            ) : (
              <div className="text-sm text-noir-300 font-mono">使用 LLM API Key（預設）</div>
            )}
          </div>

          {/* Embedding Base URL */}
          <div className="bg-noir-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-noir-500 mb-1">Base URL</div>
              {!editingEmbeddingBaseUrl && (
                <button
                  onClick={() => setEditingEmbeddingBaseUrl(true)}
                  className="text-xs text-brass-400 hover:text-brass-300"
                >
                  編輯
                </button>
              )}
            </div>
            {editingEmbeddingBaseUrl ? (
              <div className="flex items-center gap-2 mt-2">
                <input
                  type="text"
                  value={newEmbeddingBaseUrl}
                  onChange={(e) => setNewEmbeddingBaseUrl(e.target.value)}
                  placeholder="留空使用 OpenAI 預設，或輸入自訂 URL..."
                  className="flex-1 bg-noir-700 border border-noir-600 rounded px-3 py-2 text-sm text-noir-200"
                />
                <button onClick={handleSaveEmbeddingBaseUrl} className="btn btn-primary text-sm">儲存</button>
                <button
                  onClick={() => { setEditingEmbeddingBaseUrl(false); setNewEmbeddingBaseUrl(''); }}
                  className="btn btn-secondary text-sm"
                >
                  取消
                </button>
              </div>
            ) : (
              <div className="text-sm text-noir-300">OpenAI (預設)</div>
            )}
          </div>
        </div>

        <p className="mt-4 text-xs text-noir-500">
          注意：變更 Embedding 模型後需要重新索引所有文件
        </p>
      </div>

      {/* Usage Stats */}
      {usageStats && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-noir-100 mb-4">使用統計</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-brass-400">{usageStats.queries_count}</div>
              <div className="text-xs text-noir-500">查詢次數</div>
            </div>
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-noir-200">{usageStats.total_tokens.toLocaleString()}</div>
              <div className="text-xs text-noir-500">總 Tokens</div>
            </div>
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-jade-400">${usageStats.total_cost.toFixed(4)}</div>
              <div className="text-xs text-noir-500">總成本 (USD)</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderDocumentsTab = () => (
    <div className="space-y-6">
      {/* Index Status */}
      {indexStatus && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-noir-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
              </svg>
              索引狀態
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleReindex(false)}
                disabled={reindexing}
                className="btn btn-secondary text-sm"
              >
                {reindexing ? '索引中...' : '重新索引'}
              </button>
              <button
                onClick={() => handleReindex(true)}
                disabled={reindexing}
                className="btn btn-primary text-sm"
              >
                索引 + 提取元資料
              </button>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-4">
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-brass-400">{indexStatus.total_documents}</div>
              <div className="text-xs text-noir-500">總文件數</div>
            </div>
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-jade-400">{indexStatus.indexed_documents}</div>
              <div className="text-xs text-noir-500">已索引</div>
            </div>
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-noir-300">{indexStatus.pending_documents}</div>
              <div className="text-xs text-noir-500">待處理</div>
            </div>
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-vermilion-400">{indexStatus.error_documents}</div>
              <div className="text-xs text-noir-500">錯誤</div>
            </div>
            <div className="text-center p-4 bg-noir-800/50 rounded-lg">
              <div className="text-2xl font-bold text-noir-200">{indexStatus.total_chunks.toLocaleString()}</div>
              <div className="text-xs text-noir-500">總 Chunks</div>
            </div>
          </div>

          {indexStatus.last_indexed_at && (
            <div className="mt-4 text-xs text-noir-500">
              最後索引時間: {new Date(indexStatus.last_indexed_at).toLocaleString('zh-TW')}
            </div>
          )}
        </div>
      )}

      {/* Directory Structure & Auto-Discovery */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-noir-100 flex items-center gap-2">
            <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
            </svg>
            文件目錄
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={handleScanPreview}
              disabled={scanning}
              className="btn btn-secondary text-sm"
            >
              {scanning ? '掃描中...' : '檢查新檔案'}
            </button>
            <button
              onClick={() => handleScanAndIndex(false)}
              disabled={scanning}
              className="btn btn-primary text-sm"
            >
              掃描並索引
            </button>
          </div>
        </div>

        {/* Directory Info */}
        {directoryStructure && (
          <div className="space-y-4">
            {/* Base Path */}
            <div className="bg-noir-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-noir-500 mb-1">文件目錄路徑</div>
                  <div className="text-sm text-brass-400 font-mono">{directoryStructure.base_path}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-noir-200">{directoryStructure.total_files} 檔案</div>
                  <div className="text-xs text-noir-500">{(directoryStructure.total_size_bytes / 1024).toFixed(1)} KB</div>
                </div>
              </div>
            </div>

            {/* Subdirectories */}
            {directoryStructure.directories.length > 0 && (
              <div>
                <div className="text-xs text-noir-500 mb-2">子目錄 ({directoryStructure.directories.length})</div>
                <div className="space-y-2">
                  {directoryStructure.directories.map((dir) => (
                    <div
                      key={dir.path}
                      className="flex items-center justify-between p-3 bg-noir-800/30 rounded-lg border border-noir-700/50"
                    >
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-brass-500/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
                        </svg>
                        <span className="text-sm text-noir-200">{dir.name}</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-noir-500">
                        <span>{dir.file_count} 檔案</span>
                        <span>{(dir.total_size_bytes / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className="text-xs text-noir-500">
              將文件放入此目錄或其子目錄，點擊「檢查新檔案」即可自動發現新文件。
            </p>
          </div>
        )}

        {/* Scan Result */}
        {scanResult && (
          <div className="mt-4 p-4 bg-noir-800/30 rounded-lg border border-brass-500/20">
            <div className="flex items-center gap-2 mb-3">
              <svg className="w-4 h-4 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
              </svg>
              <span className="text-sm font-medium text-brass-400">掃描結果</span>
            </div>
            <div className="grid grid-cols-4 gap-3 text-center">
              <div className="p-2 bg-noir-900/50 rounded">
                <div className="text-lg font-bold text-noir-200">{scanResult.total_files_found}</div>
                <div className="text-2xs text-noir-500">總檔案</div>
              </div>
              <div className="p-2 bg-noir-900/50 rounded">
                <div className="text-lg font-bold text-brass-400">{scanResult.new_files}</div>
                <div className="text-2xs text-noir-500">新檔案</div>
              </div>
              <div className="p-2 bg-noir-900/50 rounded">
                <div className="text-lg font-bold text-jade-400">{scanResult.indexed_files}</div>
                <div className="text-2xs text-noir-500">已索引</div>
              </div>
              <div className="p-2 bg-noir-900/50 rounded">
                <div className="text-lg font-bold text-vermilion-400">{scanResult.failed_files}</div>
                <div className="text-2xs text-noir-500">失敗</div>
              </div>
            </div>
            {scanResult.new_file_list.length > 0 && scanResult.indexed_files === 0 && (
              <div className="mt-3">
                <div className="text-xs text-noir-500 mb-1">新發現的檔案：</div>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {scanResult.new_file_list.slice(0, 10).map((file, idx) => (
                    <div key={idx} className="text-xs text-noir-400 font-mono truncate">
                      {file.split('/').pop()}
                    </div>
                  ))}
                  {scanResult.new_file_list.length > 10 && (
                    <div className="text-xs text-noir-500">
                      ...還有 {scanResult.new_file_list.length - 10} 個檔案
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleScanAndIndex(false)}
                  disabled={scanning}
                  className="mt-3 btn btn-primary text-sm w-full"
                >
                  索引這些新檔案
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-noir-100">文件列表</h3>
          <span className="text-xs text-noir-500">共 {documents.length} 個文件</span>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-8 text-noir-500">
            尚無文件。請透過 CLI 或上傳功能新增文件。
          </div>
        ) : (
          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-noir-800/50 rounded-lg hover:bg-noir-800/70 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <div className="text-sm text-noir-200 font-medium truncate">{doc.name}</div>
                    {doc.issuing_authority && (
                      <span className="text-xs text-brass-400/80 bg-brass-500/10 px-1.5 py-0.5 rounded">
                        {doc.issuing_authority}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center flex-wrap gap-2 mt-1.5 text-xs text-noir-500">
                    <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                    <span className="text-noir-600">|</span>
                    <span>{doc.chunk_count} chunks</span>
                    {doc.document_type && (
                      <>
                        <span className="text-noir-600">|</span>
                        <span className="badge badge-neutral text-2xs">{doc.document_type}</span>
                      </>
                    )}
                    <span className={`badge text-2xs ${doc.indexed ? 'badge-jade' : 'badge-neutral'}`}>
                      {doc.indexed ? '已索引' : '未索引'}
                    </span>
                    {doc.metadata_extracted && (
                      <span className="badge badge-brass text-2xs">元資料已提取</span>
                    )}
                  </div>
                  {/* Additional metadata row */}
                  {(doc.violation_types?.length || doc.penalty_amount) && (
                    <div className="flex items-center gap-2 mt-1 text-xs">
                      {doc.violation_types && doc.violation_types.length > 0 && (
                        <span className="text-vermilion-400/70">
                          {doc.violation_types.slice(0, 2).join('、')}
                          {doc.violation_types.length > 2 && `...+${doc.violation_types.length - 2}`}
                        </span>
                      )}
                      {doc.penalty_amount && (
                        <span className="text-jade-400/70">{doc.penalty_amount}</span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 ml-3">
                  {doc.extraction_confidence != null && doc.extraction_confidence > 0 && (
                    <div className="text-right">
                      <div className="text-xs text-noir-500">信心度</div>
                      <div className={`text-sm font-medium ${
                        doc.extraction_confidence >= 0.8 ? 'text-jade-400' :
                        doc.extraction_confidence >= 0.5 ? 'text-brass-400' : 'text-vermilion-400'
                      }`}>
                        {(doc.extraction_confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  )}
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="p-1.5 text-noir-500 hover:text-vermilion-400 transition-colors"
                    title="刪除文件"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderSystemTab = () => (
    <div className="space-y-6">
      {/* Create Preset */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-noir-100">設定預設</h3>
          <button
            onClick={() => setShowCreatePreset(true)}
            className="btn btn-primary text-sm"
          >
            新增預設
          </button>
        </div>

        {showCreatePreset && (
          <div className="mb-4 p-4 bg-noir-800/50 rounded-lg">
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={newPresetName}
                onChange={(e) => setNewPresetName(e.target.value)}
                placeholder="預設名稱..."
                className="flex-1 bg-noir-700 border border-noir-600 rounded-lg px-3 py-2 text-sm text-noir-200"
              />
              <button onClick={handleCreatePreset} className="btn btn-primary text-sm">
                建立
              </button>
              <button
                onClick={() => { setShowCreatePreset(false); setNewPresetName(''); }}
                className="btn btn-secondary text-sm"
              >
                取消
              </button>
            </div>
            <div className="text-xs text-noir-500 mt-2">
              將儲存目前的 LLM 設定 ({activeLLM?.model})
            </div>
          </div>
        )}

        {/* Presets List */}
        <div className="space-y-2">
          {presets.length === 0 ? (
            <div className="text-center py-4 text-noir-500 text-sm">
              尚無預設。點擊「新增預設」儲存目前設定。
            </div>
          ) : (
            presets.map((preset) => (
              <div
                key={preset.id}
                className={`flex items-center justify-between p-4 rounded-lg border ${
                  preset.is_active
                    ? 'bg-brass-500/10 border-brass-500/30'
                    : 'bg-noir-800/50 border-noir-700'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-noir-200 font-medium">{preset.name}</span>
                    {preset.is_active && (
                      <span className="badge badge-brass text-2xs">使用中</span>
                    )}
                    <span className="badge badge-neutral text-2xs">{preset.config_type}</span>
                  </div>
                  <div className="text-xs text-noir-500 mt-1">
                    {preset.model} | {preset.api_key || '無 API Key'}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {!preset.is_active && (
                    <button
                      onClick={() => handleActivatePreset(preset.id)}
                      className="text-xs text-brass-400 hover:text-brass-300"
                    >
                      啟用
                    </button>
                  )}
                  <button
                    onClick={() => handleDeletePreset(preset.id)}
                    className="text-xs text-vermilion-400 hover:text-vermilion-300"
                  >
                    刪除
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* System Prompts */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-noir-100 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
          </svg>
          系統提示詞 (System Prompts)
        </h3>
        <p className="text-xs text-noir-500 mb-4">
          自訂 AI 代理的行為和回應風格。變更後將影響所有後續查詢。
        </p>

        <div className="space-y-6">
          {/* Query Analyzer Prompt */}
          <div className="bg-noir-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="text-sm font-medium text-noir-200">問題理解提示詞</div>
                <div className="text-xs text-noir-500">用於分析和理解使用者查詢的系統提示</div>
              </div>
              {!editingQueryAnalyzerPrompt && (
                <button
                  onClick={() => {
                    setEditingQueryAnalyzerPrompt(true);
                    setNewQueryAnalyzerPrompt(queryAnalyzerPrompt);
                  }}
                  className="text-xs text-brass-400 hover:text-brass-300"
                >
                  編輯
                </button>
              )}
            </div>
            {editingQueryAnalyzerPrompt ? (
              <div className="mt-3">
                <textarea
                  value={newQueryAnalyzerPrompt}
                  onChange={(e) => setNewQueryAnalyzerPrompt(e.target.value)}
                  placeholder="輸入問題理解的系統提示詞...&#10;&#10;例如：&#10;你是一個金融法律專家，專門分析台灣銀行相關的法規與裁罰案例..."
                  rows={6}
                  className="w-full bg-noir-700 border border-noir-600 rounded-lg px-3 py-2 text-sm text-noir-200 resize-y min-h-[120px]"
                />
                <div className="flex items-center justify-end gap-2 mt-3">
                  <button
                    onClick={() => { setEditingQueryAnalyzerPrompt(false); setNewQueryAnalyzerPrompt(''); }}
                    className="btn btn-secondary text-sm"
                  >
                    取消
                  </button>
                  <button onClick={handleSaveQueryAnalyzerPrompt} className="btn btn-primary text-sm">
                    儲存
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-2">
                {!queryAnalyzerPrompt && (
                  <div className="text-2xs text-brass-500/70 mb-1 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    系統預設
                  </div>
                )}
                <div className="text-sm text-noir-400 bg-noir-900/50 rounded p-3 max-h-32 overflow-y-auto whitespace-pre-wrap">
                  {queryAnalyzerPrompt || DEFAULT_QUERY_ANALYZER_PROMPT}
                </div>
              </div>
            )}
          </div>

          {/* Reporter Prompt */}
          <div className="bg-noir-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="text-sm font-medium text-noir-200">報告生成提示詞</div>
                <div className="text-xs text-noir-500">用於生成最終研究報告的系統提示</div>
              </div>
              {!editingReporterPrompt && (
                <button
                  onClick={() => {
                    setEditingReporterPrompt(true);
                    setNewReporterPrompt(reporterPrompt);
                  }}
                  className="text-xs text-brass-400 hover:text-brass-300"
                >
                  編輯
                </button>
              )}
            </div>
            {editingReporterPrompt ? (
              <div className="mt-3">
                <textarea
                  value={newReporterPrompt}
                  onChange={(e) => setNewReporterPrompt(e.target.value)}
                  placeholder="輸入報告生成的系統提示詞...&#10;&#10;例如：&#10;你是一個專業的法律研究報告撰寫者，請使用正式的法律用語..."
                  rows={6}
                  className="w-full bg-noir-700 border border-noir-600 rounded-lg px-3 py-2 text-sm text-noir-200 resize-y min-h-[120px]"
                />
                <div className="flex items-center justify-end gap-2 mt-3">
                  <button
                    onClick={() => { setEditingReporterPrompt(false); setNewReporterPrompt(''); }}
                    className="btn btn-secondary text-sm"
                  >
                    取消
                  </button>
                  <button onClick={handleSaveReporterPrompt} className="btn btn-primary text-sm">
                    儲存
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-2">
                {!reporterPrompt && (
                  <div className="text-2xs text-brass-500/70 mb-1 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    系統預設
                  </div>
                )}
                <div className="text-sm text-noir-400 bg-noir-900/50 rounded p-3 max-h-32 overflow-y-auto whitespace-pre-wrap">
                  {reporterPrompt || DEFAULT_REPORTER_PROMPT}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Info */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-noir-100 mb-4">系統資訊</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-noir-800/50 rounded-lg p-4">
            <div className="text-xs text-noir-500 mb-1">版本</div>
            <div className="text-noir-200">FinAgent v2.0</div>
          </div>
          <div className="bg-noir-800/50 rounded-lg p-4">
            <div className="text-xs text-noir-500 mb-1">後端 API</div>
            <div className="text-noir-200">{API_BASE}</div>
          </div>
        </div>
      </div>
    </div>
  );

  // ============================================
  // Main Render
  // ============================================

  return (
    <div className="min-h-screen bg-noir-950 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-display font-bold text-noir-100 flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-brass-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 011.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.56.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.893.149c-.425.07-.765.383-.93.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 01-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.397.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 01-.12-1.45l.527-.737c.25-.35.273-.806.108-1.204-.165-.397-.505-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.765-.383.93-.78.165-.398.143-.854-.107-1.204l-.527-.738a1.125 1.125 0 01.12-1.45l.773-.773a1.125 1.125 0 011.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </span>
            系統設定
          </h1>
          <p className="text-noir-400 text-sm mt-1">Settings & Configuration</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 mb-6">
          {[
            { id: 'models' as SettingsTab, label: '模型設定', icon: '🤖' },
            { id: 'documents' as SettingsTab, label: '文件管理', icon: '📄' },
            { id: 'system' as SettingsTab, label: '系統預設', icon: '⚙️' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-brass-500/20 text-brass-400 border border-brass-500/30'
                  : 'text-noir-400 hover:text-noir-200 hover:bg-noir-800'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Notifications */}
        {error && (
          <div className="mb-4 p-4 bg-vermilion-500/10 border border-vermilion-500/30 rounded-lg text-vermilion-400">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-4 bg-jade-500/10 border border-jade-500/30 rounded-lg text-jade-400">
            {success}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-10">
            <div className="flex items-center gap-3 text-noir-400">
              <div className="w-5 h-5 border-2 border-brass-500 border-t-transparent rounded-full animate-spin" />
              載入中...
            </div>
          </div>
        )}

        {/* Tab Content */}
        {!loading && (
          <>
            {activeTab === 'models' && renderModelsTab()}
            {activeTab === 'documents' && renderDocumentsTab()}
            {activeTab === 'system' && renderSystemTab()}
          </>
        )}
      </div>
    </div>
  );
}
