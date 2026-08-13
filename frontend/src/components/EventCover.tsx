import { useState } from 'react'
import { coverGradient } from '@/lib/cover'
import { cn } from '@/lib/utils'

interface EventCoverProps {
  slug: string
  coverUrl: string | null
  className?: string
  /** Rendered over the image -- the event name on the detail hero. */
  children?: React.ReactNode
}

/**
 * An event's cover. Falls back to a gradient derived from the slug when
 * `cover_url` is null or the image fails to load, so a race without a photo
 * still gets a distinct, stable look instead of an empty grey box.
 */
export function EventCover({ slug, coverUrl, className, children }: EventCoverProps) {
  const [failed, setFailed] = useState(false)
  const showImage = Boolean(coverUrl) && !failed

  return (
    <div
      className={cn('relative overflow-hidden bg-card', className)}
      style={{ background: coverGradient(slug) }}
    >
      {showImage ? (
        <img
          src={coverUrl!}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
          className="absolute inset-0 size-full object-cover"
        />
      ) : (
        <div className="course-texture absolute inset-0" />
      )}
      {children}
    </div>
  )
}
