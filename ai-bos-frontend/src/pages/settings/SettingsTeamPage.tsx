import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageHeader } from '@/components/shared/PageHeader';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useI18n } from '@/lib/i18n/store';
import { useEffect, useState } from 'react';
import { Search, UserPlus, Loader2, X } from 'lucide-react';
import { initials } from '@/lib/utils';
import { createInvitation, getInvitations, getTeamMembers, revokeInvitation } from '@/lib/api/services';
import type { Invitation, TeamMember } from '@/lib/api/types';
import { toast } from 'sonner';

export function SettingsTeamPage() {
  const { t } = useI18n();
  const [search, setSearch] = useState('');
  const [inviteOpen, setInviteOpen] = useState(false);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('staff');
  const [inviteToken, setInviteToken] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [team, invites] = await Promise.all([getTeamMembers(), getInvitations()]);
      setMembers(team);
      setInvitations(invites.filter((i) => i.status === 'pending'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const filtered = members.filter(
    (m) =>
      !search ||
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.email.toLowerCase().includes(search.toLowerCase()),
  );

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const invitation = await createInvitation({ email: inviteEmail.trim(), role: inviteRole });
      setInviteToken(invitation.token || null);
      setInviteEmail('');
      setInviteRole('staff');
      await load();
      toast.success('Invitation envoyée');
      if (!invitation.token) setInviteOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'invitation");
    } finally {
      setSaving(false);
    }
  };

  const handleRevoke = async (invitationId: string) => {
    setSaving(true);
    setError(null);
    try {
      await revokeInvitation(invitationId);
      await load();
      toast.success('Invitation révoquée');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible de révoquer');
      toast.error(err instanceof Error ? err.message : 'Impossible de révoquer');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PageHeader
        title={t('nav.settingsTeam')}
        description="Gérez les membres et rôles"
        actions={
          <Button
            onClick={() => {
              setInviteToken(null);
              setInviteOpen(true);
            }}
          >
            <UserPlus className="h-4 w-4" />
            Inviter
          </Button>
        }
      />

      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

      <Card>
        <CardContent className="p-0">
          <div className="p-4 border-b border-border">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Rechercher..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
          {loading ? (
            <div className="flex items-center justify-center p-10">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Membre</TableHead>
                  <TableHead>Rôle</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9">
                          <AvatarFallback className="bg-primary-100 text-xs text-primary-700">
                            {initials(m.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">{m.name}</p>
                          <p className="text-xs text-muted-foreground">{m.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="muted" className="capitalize">
                        {m.role.replace(/_/g, ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={m.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {invitations.length > 0 && (
        <Card className="mt-6">
          <CardContent className="p-4">
            <h2 className="mb-3 text-sm font-semibold">Invitations en attente</h2>
            <ul className="space-y-2">
              {invitations.map((inv) => (
                <li key={inv.id} className="flex items-center justify-between gap-3 text-sm">
                  <span>
                    {inv.email} · <span className="capitalize text-muted-foreground">{inv.role.replace(/_/g, ' ')}</span>
                  </span>
                  <div className="flex items-center gap-2">
                    <Badge variant="muted">{inv.status}</Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={saving}
                      onClick={() => void handleRevoke(inv.id)}
                    >
                      <X className="h-4 w-4" />
                      Révoquer
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Dialog
        open={inviteOpen}
        onOpenChange={(open) => {
          setInviteOpen(open);
          if (!open) setInviteToken(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Inviter un membre</DialogTitle>
            <DialogDescription>Envoyez une invitation par email</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="collegue@entreprise.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Rôle</Label>
              <Select value={inviteRole} onValueChange={setInviteRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="sales_manager">Sales Manager</SelectItem>
                  <SelectItem value="finance_manager">Finance Manager</SelectItem>
                  <SelectItem value="staff">Staff</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {inviteToken && (
              <p className="rounded-md bg-muted p-2 text-xs break-all">
                Lien d'acceptation (mock email) : token <code>{inviteToken}</code>
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setInviteOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleInvite} disabled={saving || !inviteEmail.trim()}>
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              {t('common.send')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
