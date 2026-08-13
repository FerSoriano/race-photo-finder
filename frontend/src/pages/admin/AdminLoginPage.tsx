import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { verifyAdminKey } from '@/api/client'
import { saveAdminKey } from '@/lib/adminAuth'
import { BibMark } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

/**
 * Probes the candidate key against the API before ever writing it to
 * localStorage -- a typo that gets persisted would leave every later screen
 * 401ing with no obvious cause.
 */
export function AdminLoginPage() {
  const [value, setValue] = useState('')

  const mutation = useMutation({
    mutationFn: (key: string) => verifyAdminKey(key),
    onSuccess: (_stats, key) => saveAdminKey(key),
  })

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    const key = value.trim()
    if (key) mutation.mutate(key)
  }

  return (
    <main className="grid min-h-dvh place-items-center px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-xl border border-border bg-card p-6"
      >
        <div className="flex flex-col items-center text-center">
          <BibMark />
          <h1 className="mt-4 font-heading text-lg font-bold">Panel de administración</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Pega la llave de administrador para continuar.
          </p>
        </div>

        <div className="mt-6 flex flex-col gap-1.5">
          <Label htmlFor="admin-key">Llave de administrador</Label>
          <Input
            id="admin-key"
            type="password"
            autoFocus
            autoComplete="off"
            spellCheck={false}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            aria-invalid={mutation.isError || undefined}
          />
          {mutation.isError && (
            <p className="text-sm text-destructive">
              Llave inválida. Revisa ADMIN_API_KEY en el .env del backend.
            </p>
          )}
        </div>

        <Button
          type="submit"
          className="mt-5 w-full font-heading font-bold"
          size="lg"
          disabled={!value.trim() || mutation.isPending}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Verificando…
            </>
          ) : (
            'Entrar'
          )}
        </Button>
      </form>
    </main>
  )
}
