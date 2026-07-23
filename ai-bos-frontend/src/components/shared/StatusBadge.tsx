import { Badge, badgeVariants } from '@/components/ui/badge';
import type { VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

type BadgeVariant = VariantProps<typeof badgeVariants>['variant'];

const STATUS_MAP: Record<string, BadgeVariant> = {
  active: 'success',
  paid: 'success',
  won: 'success',
  completed: 'success',
  resolved: 'success',
  hired: 'success',
  done: 'success',
  in_stock: 'success',
  received: 'success',
  approved: 'success',
  open: 'default',
  sent: 'default',
  accepted: 'default',
  fulfilled: 'default',
  invoiced: 'default',
  qualified: 'default',
  proposal: 'default',
  negotiation: 'default',
  screening: 'default',
  interview: 'default',
  offer: 'default',
  submitted: 'default',
  upcoming: 'default',
  draft: 'muted',
  pending: 'warning',
  review: 'warning',
  in_progress: 'warning',
  on_hold: 'warning',
  paused: 'warning',
  scheduled: 'warning',
  low_stock: 'warning',
  expiring: 'warning',
  on_leave: 'warning',
  overdue: 'danger',
  lost: 'danger',
  cancelled: 'danger',
  canceled: 'danger',
  rejected: 'danger',
  expired: 'danger',
  out_of_stock: 'danger',
  terminated: 'danger',
  error: 'danger',
  inactive: 'muted',
  archived: 'muted',
  closed: 'muted',
  lead: 'secondary',
  new: 'default',
  applied: 'muted',
  planning: 'secondary',
  idle: 'muted',
  success: 'success',
  running: 'warning',
};

/** French labels for common English status codes used in API/mocks. */
const STATUS_LABEL_FR: Record<string, string> = {
  active: 'Actif',
  inactive: 'Inactif',
  paid: 'Payée',
  sent: 'Envoyée',
  overdue: 'En retard',
  draft: 'Brouillon',
  pending: 'En attente',
  resolved: 'Résolu',
  completed: 'Terminée',
  cancelled: 'Annulée',
  canceled: 'Annulée',
  upcoming: 'À venir',
  open: 'Ouverte',
  paused: 'En pause',
  closed: 'Fermée',
  terminated: 'Terminé',
  on_leave: 'En congé',
  submitted: 'Soumise',
  approved: 'Approuvée',
  received: 'Reçue',
  rejected: 'Rejetée',
  won: 'Gagné',
  lost: 'Perdu',
  new: 'Nouveau',
  qualified: 'Qualifié',
  proposal: 'Proposition',
  negotiation: 'Négociation',
  in_progress: 'En cours',
  review: 'Revue',
  done: 'Terminé',
  todo: 'À faire',
  success: 'Succès',
  error: 'Erreur',
  running: 'En cours',
  hired: 'Embauché',
  screening: 'Présélection',
  interview: 'Entretien',
  offer: 'Offre',
  applied: 'Candidature',
  scheduled: 'Planifié',
  fulfilled: 'Livrée',
  invoiced: 'Facturée',
  accepted: 'Acceptée',
  expired: 'Expirée',
  archived: 'Archivé',
  idle: 'Inactif',
  planning: 'Planification',
  on_hold: 'En pause',
  low_stock: 'Stock bas',
  out_of_stock: 'Rupture',
  in_stock: 'En stock',
  full_time: 'Temps plein',
  part_time: 'Temps partiel',
  contract: 'Contrat',
  internship: 'Stage',
};

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const key = (status || '').trim().toLowerCase().replace(/\s+/g, '_');
  const variant = STATUS_MAP[key] || STATUS_MAP[status] || 'default';
  const display =
    label ||
    STATUS_LABEL_FR[key] ||
    STATUS_LABEL_FR[status] ||
    status.replace(/_/g, ' ');
  return (
    <Badge variant={variant} className={cn('font-medium')}>
      {display}
    </Badge>
  );
}
