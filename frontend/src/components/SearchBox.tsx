import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface SearchBoxProps {
  defaultValue: string
  onSearch: (bib: string) => void
}

export function SearchBox({ defaultValue, onSearch }: SearchBoxProps) {
  const [value, setValue] = useState(defaultValue)

  useEffect(() => setValue(defaultValue), [defaultValue])

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (value.trim()) onSearch(value.trim())
      }}
      className="flex gap-2"
    >
      <Input
        inputMode="numeric"
        placeholder="Tu número de corredor"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="h-12 flex-1 text-lg"
        aria-label="Número de corredor"
      />
      <Button type="submit" size="lg" className="h-12 px-6 text-base">
        Buscar
      </Button>
    </form>
  )
}
