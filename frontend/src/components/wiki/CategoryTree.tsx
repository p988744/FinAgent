import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, ChevronDown, Tag, Loader2, AlertCircle } from 'lucide-react'
import type { CategoryTree as CategoryTreeType, CategorySummary } from '../../types/wiki'

interface CategoryTreeProps {
  onCategorySelect?: (category: CategorySummary) => void
  selectedCategoryId?: number
}

export function CategoryTree({ onCategorySelect, selectedCategoryId }: CategoryTreeProps) {
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set(['authority']))
  const [selectedType, setSelectedType] = useState<'authority' | 'institution' | 'violation' | 'doc_type'>('authority')

  const categoryTypes: Array<{
    type: 'authority' | 'institution' | 'violation' | 'doc_type'
    label: string
    icon: string
  }> = [
    { type: 'authority', label: '主管機關', icon: '🏛️' },
    { type: 'institution', label: '金融機構', icon: '🏦' },
    { type: 'violation', label: '違規類型', icon: '⚠️' },
    { type: 'doc_type', label: '文件類型', icon: '📄' },
  ]

  // Fetch categories for the selected type
  const { data, isLoading, error } = useQuery<CategoryTreeType>({
    queryKey: ['wiki-categories', selectedType],
    queryFn: async () => {
      const response = await fetch(`/api/v1/wiki/categories?type=${selectedType}`)
      if (!response.ok) {
        throw new Error('Failed to fetch categories')
      }
      return response.json()
    },
  })

  const toggleType = (type: string) => {
    setExpandedTypes((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(type)) {
        newSet.delete(type)
      } else {
        newSet.add(type)
      }
      return newSet
    })
  }

  const handleTypeClick = (type: 'authority' | 'institution' | 'violation' | 'doc_type') => {
    setSelectedType(type)
    if (!expandedTypes.has(type)) {
      toggleType(type)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <Tag className="h-5 w-5 mr-2 text-blue-600" />
        分類瀏覽
      </h2>

      <div className="space-y-2">
        {categoryTypes.map(({ type, label, icon }) => {
          const isExpanded = expandedTypes.has(type)
          const isSelected = type === selectedType

          return (
            <div key={type}>
              {/* Category Type Header */}
              <button
                onClick={() => handleTypeClick(type)}
                className={`w-full flex items-center justify-between p-2 rounded-md transition-colors ${
                  isSelected
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-2">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <span className="text-lg">{icon}</span>
                  <span className="font-medium text-sm">{label}</span>
                </div>
                {type === selectedType && data && (
                  <span className="text-xs font-semibold px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                    {data.total_count}
                  </span>
                )}
              </button>

              {/* Category Items */}
              {isExpanded && type === selectedType && (
                <div className="ml-6 mt-1 space-y-1">
                  {isLoading && (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-4 w-4 animate-spin text-blue-600 mr-2" />
                      <span className="text-sm text-gray-600">載入中...</span>
                    </div>
                  )}

                  {error && (
                    <div className="text-sm text-red-600 py-2 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      載入失敗
                    </div>
                  )}

                  {data?.categories.map((category) => {
                    const isActive = category.id === selectedCategoryId

                    return (
                      <button
                        key={category.id}
                        onClick={() => onCategorySelect?.(category)}
                        className={`w-full text-left p-2 rounded-md text-sm transition-colors ${
                          isActive
                            ? 'bg-blue-100 text-blue-900 font-medium'
                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="truncate flex-1">{category.name}</span>
                          <span className="text-xs text-gray-500 ml-2">
                            {category.document_count}
                          </span>
                        </div>
                        {category.keywords.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {category.keywords.slice(0, 3).map((keyword, idx) => (
                              <span
                                key={idx}
                                className="inline-block px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
