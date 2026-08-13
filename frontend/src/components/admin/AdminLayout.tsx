import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { CalendarRange, ExternalLink, LayoutDashboard, LogOut } from 'lucide-react'
import { clearAdminKey } from '@/lib/adminAuth'
import { BibMark } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface AdminLayoutProps {
  children: ReactNode
}

/**
 * The panel's shell. Desktop-first by decision -- unlike the public app, this
 * is only ever opened by the photographer from a computer, so it does not
 * reuse the mobile-first <Layout/>. Uses the --sidebar-* tokens already
 * defined in index.css, which had no consumer until this.
 */
export function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div className="min-h-dvh md:grid md:grid-cols-[15rem_1fr]">
      <aside className="flex flex-col border-b border-sidebar-border bg-sidebar text-sidebar-foreground md:sticky md:top-0 md:h-dvh md:border-r md:border-b-0">
        <div className="flex items-center gap-2 px-4 py-4">
          <BibMark />
          <span className="font-heading text-[0.8125rem] font-bold tracking-[0.14em] uppercase">
            Panel
          </span>
        </div>

        <nav className="flex flex-col gap-0.5 px-2">
          <AdminNavLink to="/admin" end icon={<LayoutDashboard className="size-4" />}>
            Resumen
          </AdminNavLink>
          <AdminNavLink to="/admin/eventos" icon={<CalendarRange className="size-4" />}>
            Carreras
          </AdminNavLink>
        </nav>

        <div className="mt-auto flex flex-col gap-1 border-t border-sidebar-border p-2">
          <Button
            variant="ghost"
            nativeButton={false}
            className="justify-start text-sidebar-foreground hover:bg-sidebar-accent"
            render={<a href="/" />}
          >
            <ExternalLink className="size-4" />
            Ver el sitio
          </Button>
          <Button
            variant="ghost"
            className="justify-start text-sidebar-foreground hover:bg-sidebar-accent"
            onClick={() => clearAdminKey()}
          >
            <LogOut className="size-4" />
            Cerrar sesión
          </Button>
        </div>
      </aside>

      <main className="min-w-0 px-6 py-8 md:px-10 md:py-10">{children}</main>
    </div>
  )
}

function AdminNavLink({
  to,
  end,
  icon,
  children,
}: {
  to: string
  end?: boolean
  icon: ReactNode
  children: ReactNode
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors',
          isActive
            ? 'bg-sidebar-accent text-sidebar-accent-foreground'
            : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
        )
      }
    >
      {icon}
      {children}
    </NavLink>
  )
}
