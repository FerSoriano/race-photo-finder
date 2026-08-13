import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { EmptyBib } from '@/components/EmptyBib'

export function NotFoundPage() {
  return (
    <main className="mx-auto flex max-w-md flex-col items-center px-4 py-16 text-center sm:py-24">
      <EmptyBib label="404" />
      <h1 className="mt-8 font-heading text-2xl font-bold tracking-tight">
        Esta página no existe
      </h1>
      <p className="mt-2 text-muted-foreground">
        Puede que el enlace esté incompleto. Revisa el que te compartieron, o
        busca tu carrera en la lista.
      </p>
      <Button
        size="lg"
        className="mt-6 font-heading font-bold"
        render={<Link to="/" />}
      >
        Ver las carreras
      </Button>
    </main>
  )
}
