import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface BibProps {
  eventName: string
  defaultValue: string
  onSearch: (bib: string) => void
}

/**
 * The signature element. The bib search is not an input styled like a race
 * bib -- it is the bib, and the runner writes their number on it. It is the
 * only light surface in the whole app, so the eye cannot land anywhere else.
 *
 * Underneath it stays a plain numeric input with a real label and submit, so
 * none of this costs accessibility.
 */
export function Bib({ eventName, defaultValue, onSearch }: BibProps) {
  const [value, setValue] = useState(defaultValue)

  useEffect(() => setValue(defaultValue), [defaultValue])

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (value.trim()) onSearch(value.trim())
      }}
      className="flex flex-col gap-4"
    >
      <div className="relative rounded-xl bg-dorsal px-4 pt-5 pb-7 text-dorsal-ink shadow-2xl shadow-black/40">
        <PinHoles />

        <p className="text-center font-heading text-[0.6875rem] font-bold tracking-[0.16em] text-dorsal-ink/55 uppercase">
          {eventName}
        </p>

        <label htmlFor="bib" className="sr-only">
          Tu número de corredor
        </label>
        <input
          id="bib"
          name="bib"
          type="text"
          inputMode="numeric"
          autoComplete="off"
          pattern="[0-9]*"
          maxLength={8}
          placeholder="0000"
          value={value}
          onChange={(e) => setValue(e.target.value.replace(/\D/g, ''))}
          autoFocus={defaultValue === ''}
          className={cn(
            'mt-2 w-full bg-transparent text-center outline-none',
            'font-heading text-[3rem] leading-none font-extrabold tabular-nums',
            'tracking-tight text-dorsal-ink caret-dorsal-ink',
            'placeholder:text-dorsal-ink/20 sm:text-[4rem]',
          )}
        />

        {/* the torn-off edge */}
        <div className="bib-perforation absolute inset-x-9 bottom-3 h-[2px]" />
      </div>

      <Button
        type="submit"
        size="lg"
        disabled={value.trim() === ''}
        className="h-13 w-full font-heading text-base font-bold"
      >
        Buscar mis fotos
      </Button>
    </form>
  )
}

function PinHoles() {
  return (
    <>
      <span className="bib-pin absolute top-3 left-3 size-1.5" />
      <span className="bib-pin absolute top-3 right-3 size-1.5" />
      <span className="bib-pin absolute bottom-3 left-3 size-1.5" />
      <span className="bib-pin absolute right-3 bottom-3 size-1.5" />
    </>
  )
}
