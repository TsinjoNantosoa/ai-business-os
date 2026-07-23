import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Search, MoreHorizontal, Mail, Phone, Tag,
  ChevronLeft, ChevronRight, Pencil, Trash2,
} from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { ExportMenu } from '@/components/shared/ExportMenu';
import { TableSkeleton } from '@/components/shared/Skeletons';
import { EmptyState } from '@/components/shared/EmptyState';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { createContact, deleteContact, getActivities, getContacts, updateContact } from '@/lib/api/services';
import type { Contact } from '@/lib/api/types';
import { useI18n } from '@/lib/i18n/store';
import { initials, formatRelativeTime } from '@/lib/utils';
import { useAuth } from '@/lib/auth/store';
import { toast } from 'sonner';
import type { ExportColumn } from '@/lib/export';

const PAGE_SIZE = 10;

const emptyForm = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  company: '',
  position: '',
  status: 'active',
};

export function CRMContactsPage() {
  const { t } = useI18n();
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('crm.contact.write');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [ownerFilter, setOwnerFilter] = useState<string>('all');
  const [page, setPage] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<Contact | null>(null);

  const queryClient = useQueryClient();
  const { data: contacts, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['contacts'],
    queryFn: getContacts,
  });
  const { data: activities } = useQuery({ queryKey: ['activities'], queryFn: getActivities });

  const createMutation = useMutation({
    mutationFn: createContact,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setCreateOpen(false);
      setForm(emptyForm);
      toast.success('Contact créé');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de créer le contact'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<typeof emptyForm> }) =>
      updateContact(id, payload),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setEditOpen(false);
      setEditing(null);
      setSelectedId(updated.id);
      toast.success('Contact mis à jour');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de mettre à jour le contact'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteContact,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setSelectedId(null);
      setEditOpen(false);
      toast.success('Contact supprimé');
    },
    onError: (err: Error) => toast.error(err.message || 'Impossible de supprimer le contact'),
  });

  const owners = useMemo(() => {
    const set = new Set((contacts || []).map((c) => c.ownerName).filter(Boolean) as string[]);
    return Array.from(set);
  }, [contacts]);

  const filtered = useMemo(() => {
    if (!contacts) return [];
    return contacts.filter((c) => {
      const matchSearch =
        !search ||
        `${c.firstName} ${c.lastName}`.toLowerCase().includes(search.toLowerCase()) ||
        c.email.toLowerCase().includes(search.toLowerCase()) ||
        c.company.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === 'all' || c.status === statusFilter;
      const matchOwner = ownerFilter === 'all' || c.ownerName === ownerFilter;
      return matchSearch && matchStatus && matchOwner;
    });
  }, [contacts, search, statusFilter, ownerFilter]);

  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const selectedContact = (contacts || []).find((c) => c.id === selectedId);
  const contactActivities = (activities || []).filter((a) => a.contactId === selectedId);

  const openEdit = (contact: Contact) => {
    setEditing(contact);
    setForm({
      firstName: contact.firstName,
      lastName: contact.lastName,
      email: contact.email,
      phone: contact.phone || '',
      company: contact.company,
      position: contact.position || '',
      status: contact.status,
    });
    setEditOpen(true);
  };

  const exportColumns: ExportColumn<Contact>[] = [
    { header: 'Prénom', value: (c) => c.firstName },
    { header: 'Nom', value: (c) => c.lastName },
    { header: 'Email', value: (c) => c.email },
    { header: 'Téléphone', value: (c) => c.phone || '' },
    { header: 'Entreprise', value: (c) => c.company },
    { header: 'Poste', value: (c) => c.position || '' },
    { header: 'Statut', value: (c) => c.status },
    { header: 'Responsable', value: (c) => c.ownerName || '' },
    { header: 'Tags', value: (c) => (c.tags || []).join('|') },
  ];

  return (
    <div>
      <PageHeader
        title={t('nav.crmContacts')}
        description="Gérez vos contacts et comptes clients"
        actions={
          <>
            <ExportMenu
              filename="contacts"
              title="Contacts AI BOS"
              sheetName="Contacts"
              columns={exportColumns}
              rows={filtered}
              label={t('common.export')}
            />
            {canWrite && (
              <Button
                onClick={() => {
                  setForm(emptyForm);
                  setCreateOpen(true);
                }}
              >
                <Plus className="h-4 w-4" />
                {t('common.create')}
              </Button>
            )}
          </>
        }
      />

      <Card className="mb-4">
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={t('common.search')}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="pl-9"
            />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => {
              setStatusFilter(v);
              setPage(0);
            }}
          >
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder={t('common.status')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('common.all')}</SelectItem>
              <SelectItem value="active">Actif</SelectItem>
              <SelectItem value="lead">Lead</SelectItem>
              <SelectItem value="inactive">Inactif</SelectItem>
              <SelectItem value="archived">Archivé</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={ownerFilter}
            onValueChange={(v) => {
              setOwnerFilter(v);
              setPage(0);
            }}
          >
            <SelectTrigger className="w-full sm:w-44">
              <SelectValue placeholder={t('common.owner')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('common.all')}</SelectItem>
              {owners.map((o) => (
                <SelectItem key={o} value={o}>
                  {o}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4">
              <TableSkeleton />
            </div>
          ) : isError ? (
            <EmptyState
              icon={Search}
              title="Impossible de charger les contacts"
              description={(error as Error)?.message || 'Reconnectez-vous puis réessayez.'}
              action={{ label: 'Réessayer', onClick: () => void refetch() }}
            />
          ) : filtered.length === 0 ? (
            <EmptyState icon={Search} title={t('common.noResults')} description="Aucun contact ne correspond à vos critères." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('common.name')}</TableHead>
                  <TableHead className="hidden md:table-cell">{t('common.company')}</TableHead>
                  <TableHead className="hidden lg:table-cell">Email</TableHead>
                  <TableHead>{t('common.status')}</TableHead>
                  <TableHead className="hidden lg:table-cell">{t('common.owner')}</TableHead>
                  <TableHead className="hidden xl:table-cell">Tags</TableHead>
                  <TableHead className="text-right">{t('common.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginated.map((contact) => (
                  <TableRow key={contact.id} className="cursor-pointer" onClick={() => setSelectedId(contact.id)}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9" style={{ backgroundColor: `${contact.avatarColor}20` }}>
                          <AvatarFallback style={{ color: contact.avatarColor, backgroundColor: 'transparent' }} className="text-xs font-medium">
                            {initials(`${contact.firstName} ${contact.lastName}`)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">
                            {contact.firstName} {contact.lastName}
                          </p>
                          <p className="text-xs text-muted-foreground">{contact.position}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm">{contact.company}</TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">{contact.email}</TableCell>
                    <TableCell>
                      <StatusBadge status={contact.status} />
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm">{contact.ownerName}</TableCell>
                    <TableCell className="hidden xl:table-cell">
                      <div className="flex flex-wrap gap-1">
                        {contact.tags.map((tag) => (
                          <Badge key={tag} variant="muted" className="text-2xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                            }}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                          <DropdownMenuItem onClick={() => setSelectedId(contact.id)}>Voir</DropdownMenuItem>
                          {canWrite && (
                            <DropdownMenuItem onClick={() => openEdit(contact)}>
                              <Pencil className="h-4 w-4" /> Modifier
                            </DropdownMenuItem>
                          )}
                          {canWrite && (
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => {
                                if (window.confirm(`Supprimer ${contact.firstName} ${contact.lastName} ?`)) {
                                  deleteMutation.mutate(contact.id);
                                }
                              }}
                            >
                              <Trash2 className="h-4 w-4" /> Supprimer
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {filtered.length > 0 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} sur {filtered.length}
          </p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" disabled={page === 0} onClick={() => setPage(page - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page + 1} / {totalPages}
            </span>
            <Button variant="outline" size="icon" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      <Sheet open={!!selectedId} onOpenChange={(open) => !open && setSelectedId(null)}>
        <SheetContent className="w-full overflow-y-auto scrollbar-thin sm:max-w-lg">
          {selectedContact && (
            <>
              <SheetHeader>
                <SheetTitle className="flex items-center gap-3">
                  <Avatar className="h-12 w-12" style={{ backgroundColor: `${selectedContact.avatarColor}20` }}>
                    <AvatarFallback style={{ color: selectedContact.avatarColor, backgroundColor: 'transparent' }}>
                      {initials(`${selectedContact.firstName} ${selectedContact.lastName}`)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p>
                      {selectedContact.firstName} {selectedContact.lastName}
                    </p>
                    <SheetDescription>
                      {selectedContact.position} • {selectedContact.company}
                    </SheetDescription>
                  </div>
                </SheetTitle>
              </SheetHeader>

              <div className="space-y-6 p-5">
                <div className="flex gap-2">
                  {canWrite && (
                    <Button variant="outline" size="sm" onClick={() => openEdit(selectedContact)}>
                      <Pencil className="h-4 w-4" /> Modifier
                    </Button>
                  )}
                  {canWrite && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-destructive"
                      disabled={deleteMutation.isPending}
                      onClick={() => {
                        if (window.confirm(`Supprimer ${selectedContact.firstName} ${selectedContact.lastName} ?`)) {
                          deleteMutation.mutate(selectedContact.id);
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" /> Supprimer
                    </Button>
                  )}
                </div>

                <div className="space-y-3">
                  <h4 className="text-sm font-semibold">Informations</h4>
                  <div className="grid grid-cols-1 gap-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Mail className="h-4 w-4" />
                      {selectedContact.email}
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Phone className="h-4 w-4" />
                      {selectedContact.phone || '—'}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedContact.tags.map((tag) => (
                      <Badge key={tag} variant="muted" className="gap-1 text-2xs">
                        <Tag className="h-2.5 w-2.5" />
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-sm font-semibold">Activités récentes</h4>
                  {contactActivities.length > 0 ? (
                    <div className="space-y-3">
                      {contactActivities.map((act) => (
                        <div key={act.id} className="flex gap-3 border-l-2 border-primary/20 pl-3">
                          <div>
                            <p className="text-sm font-medium">{act.description}</p>
                            <p className="text-xs text-muted-foreground">
                              {act.userName} • {formatRelativeTime(act.createdAt)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Aucune activité récente</p>
                  )}
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouveau contact</DialogTitle>
            <DialogDescription>Ajoutez un nouveau contact à votre CRM</DialogDescription>
          </DialogHeader>
          <ContactFormFields form={form} setForm={setForm} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              disabled={createMutation.isPending || !form.firstName || !form.lastName || !form.email || !form.company}
              onClick={() => createMutation.mutate(form)}
            >
              {createMutation.isPending ? 'Enregistrement…' : t('common.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier le contact</DialogTitle>
            <DialogDescription>Mettez à jour les informations du contact</DialogDescription>
          </DialogHeader>
          <ContactFormFields form={form} setForm={setForm} showStatus />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              disabled={updateMutation.isPending || !editing || !form.firstName || !form.lastName || !form.email || !form.company}
              onClick={() => {
                if (!editing) return;
                updateMutation.mutate({ id: editing.id, payload: form });
              }}
            >
              {updateMutation.isPending ? 'Enregistrement…' : t('common.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ContactFormFields({
  form,
  setForm,
  showStatus = false,
}: {
  form: typeof emptyForm;
  setForm: (v: typeof emptyForm) => void;
  showStatus?: boolean;
}) {
  return (
    <div className="grid grid-cols-2 gap-4 py-2">
      <div className="space-y-2">
        <Label htmlFor="firstName">Prénom</Label>
        <Input id="firstName" value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="lastName">Nom</Label>
        <Input id="lastName" value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} />
      </div>
      <div className="col-span-2 space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="phone">Téléphone</Label>
        <Input id="phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="company">Entreprise</Label>
        <Input id="company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
      </div>
      <div className={`space-y-2 ${showStatus ? '' : 'col-span-2'}`}>
        <Label htmlFor="position">Poste</Label>
        <Input id="position" value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })} />
      </div>
      {showStatus && (
        <div className="space-y-2">
          <Label>Statut</Label>
          <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Actif</SelectItem>
              <SelectItem value="lead">Lead</SelectItem>
              <SelectItem value="inactive">Inactif</SelectItem>
              <SelectItem value="archived">Archivé</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  );
}
