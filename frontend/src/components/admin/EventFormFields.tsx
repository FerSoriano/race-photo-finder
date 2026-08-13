import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export interface EventFormValues {
  name: string
  event_date: string
  location: string
  description: string
}

export const emptyEventFormValues: EventFormValues = {
  name: '',
  event_date: '',
  location: '',
  description: '',
}

interface EventFormFieldsProps {
  idPrefix: string
  values: EventFormValues
  onChange: (values: EventFormValues) => void
  disabled?: boolean
}

/** Shared field set for the create dialog and the edit page. Slug is
 * deliberately not here -- it is editable only at creation, read-only after. */
export function EventFormFields({ idPrefix, values, onChange, disabled }: EventFormFieldsProps) {
  const set = <K extends keyof EventFormValues>(key: K, value: EventFormValues[K]) =>
    onChange({ ...values, [key]: value })

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-name`}>Nombre</Label>
        <Input
          id={`${idPrefix}-name`}
          value={values.name}
          disabled={disabled}
          maxLength={200}
          required
          onChange={(event) => set('name', event.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-date`}>Fecha</Label>
          <Input
            id={`${idPrefix}-date`}
            type="date"
            value={values.event_date}
            disabled={disabled}
            onChange={(event) => set('event_date', event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${idPrefix}-location`}>Lugar</Label>
          <Input
            id={`${idPrefix}-location`}
            value={values.location}
            disabled={disabled}
            maxLength={200}
            onChange={(event) => set('location', event.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-description`}>Descripción</Label>
        <Textarea
          id={`${idPrefix}-description`}
          rows={3}
          value={values.description}
          disabled={disabled}
          onChange={(event) => set('description', event.target.value)}
        />
      </div>
    </div>
  )
}
