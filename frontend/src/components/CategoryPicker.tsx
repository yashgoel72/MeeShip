import { useState, useEffect, useMemo, Fragment } from 'react'
import { Combobox, Transition } from '@headlessui/react'
import { getCategories, CategoryItem } from '../services/meeshoApi'
import { useAppStore } from '../stores/appStore'

/**
 * Searchable product category picker using Headless UI Combobox.
 *
 * Fetches the full Meesho taxonomy once, then filters client-side.
 * Each row shows:  **Bold name** — gray breadcrumb path
 */
export default function CategoryPicker() {
  const sscatId = useAppStore((s) => s.sscatId)
  const sscatName = useAppStore((s) => s.sscatName)
  const sscatBreadcrumb = useAppStore((s) => s.sscatBreadcrumb)
  const setCategory = useAppStore((s) => s.setCategory)

  const [categories, setCategories] = useState<CategoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState('')

  // Rebuild a "selected" object from store (Combobox needs an object value)
  const selected: CategoryItem | null = sscatId
    ? { id: sscatId, name: sscatName ?? '', breadcrumb: sscatBreadcrumb ?? '' }
    : null

  // Fetch categories once on mount
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getCategories()
      .then((data) => {
        if (!cancelled) setCategories(data)
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Client-side fuzzy filter on name + breadcrumb
  const filtered = useMemo(() => {
    if (!query) return categories.slice(0, 80) // show top 80 when empty
    const q = query.toLowerCase()
    return categories
      .filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.breadcrumb.toLowerCase().includes(q)
      )
      .slice(0, 80)
  }, [categories, query])

  const handleChange = (item: CategoryItem | null) => {
    if (item) {
      setCategory(item.id, item.name, item.breadcrumb)
    } else {
      setCategory(null, null, null)
    }
    setQuery('')
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      <Combobox value={selected} onChange={handleChange} nullable>
        <div className="relative">
          {/* Label */}
          <label className="mb-1.5 flex items-center gap-2 text-sm font-semibold text-slate-700">
            <span className="text-base">🏷️</span>
            Product Category
            {!selected && (
              <span className="text-xs font-normal text-rose-500">(required)</span>
            )}
          </label>

          {/* Input */}
          <div className="relative">
            <Combobox.Input
              className={`w-full rounded-xl border py-3 pl-4 pr-10 text-sm transition-all focus:outline-none focus:ring-2 ${
                selected
                  ? 'border-emerald-200 bg-emerald-50/50 text-slate-900 focus:border-emerald-400 focus:ring-emerald-200'
                  : 'border-slate-200 bg-white text-slate-900 focus:border-meesho focus:ring-meesho/20'
              }`}
              displayValue={(item: CategoryItem | null) =>
                item ? `${item.name}  —  ${item.breadcrumb}` : ''
              }
              onChange={(e) => setQuery(e.target.value)}
              placeholder={loading ? 'Loading categories…' : 'Search category (e.g. Tshirts, Sarees, Shoes)…'}
            />

            {/* Clear button when something is selected */}
            {selected && (
              <button
                type="button"
                onClick={() => handleChange(null)}
                className="absolute inset-y-0 right-8 flex items-center px-1 text-slate-400 hover:text-slate-600"
                title="Clear selection"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}

            {/* Chevron */}
            <Combobox.Button className="absolute inset-y-0 right-0 flex items-center pr-3">
              <svg className="h-5 w-5 text-slate-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 3a.75.75 0 01.55.24l3.25 3.5a.75.75 0 11-1.1 1.02L10 4.852 7.3 7.76a.75.75 0 01-1.1-1.02l3.25-3.5A.75.75 0 0110 3zm-3.76 9.2a.75.75 0 011.06.04l2.7 2.908 2.7-2.908a.75.75 0 111.1 1.02l-3.25 3.5a.75.75 0 01-1.1 0l-3.25-3.5a.75.75 0 01.04-1.06z"
                  clipRule="evenodd"
                />
              </svg>
            </Combobox.Button>
          </div>

          {/* Dropdown */}
          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
            afterLeave={() => setQuery('')}
          >
            <Combobox.Options className="absolute z-30 mt-1 max-h-60 w-full overflow-auto rounded-xl bg-white py-1 text-sm shadow-lg ring-1 ring-slate-200 focus:outline-none">
              {loading ? (
                <div className="px-4 py-3 text-slate-500">Loading categories…</div>
              ) : filtered.length === 0 ? (
                <div className="px-4 py-3 text-slate-500">
                  {query ? `No categories matching "${query}"` : 'No categories available'}
                </div>
              ) : (
                filtered.map((cat) => (
                  <Combobox.Option
                    key={cat.id}
                    value={cat}
                    className={({ active }) =>
                      `cursor-pointer select-none px-4 py-2.5 ${
                        active ? 'bg-meesho/10 text-meesho' : 'text-slate-900'
                      }`
                    }
                  >
                    {({ selected: isSelected, active }) => (
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <span className={`font-semibold ${active ? 'text-meesho' : 'text-slate-900'}`}>
                            {cat.name}
                          </span>
                          <span className={`ml-2 text-xs ${active ? 'text-meesho/60' : 'text-slate-400'}`}>
                            {cat.breadcrumb}
                          </span>
                        </div>
                        {isSelected && (
                          <svg className="h-4 w-4 shrink-0 text-meesho" viewBox="0 0 20 20" fill="currentColor">
                            <path
                              fillRule="evenodd"
                              d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </div>
                    )}
                  </Combobox.Option>
                ))
              )}
            </Combobox.Options>
          </Transition>
        </div>
      </Combobox>

      {/* Selected category chip */}
      {selected && (
        <div className="mt-2 flex items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
            <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                clipRule="evenodd"
              />
            </svg>
            {selected.name}
          </span>
          <span className="text-xs text-slate-400">{selected.breadcrumb}</span>
        </div>
      )}
    </div>
  )
}
