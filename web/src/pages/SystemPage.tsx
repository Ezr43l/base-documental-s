import { CheckCircle2, Clock3, Database, GitBranch, HardDrive, Network, RefreshCw, Server, Settings, ShieldCheck, XCircle } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { ErrorState, LoadingState, PageHeader } from '../components/Feedback'
import { ContentCard } from '../layout/AppShell'
import { useAuth } from '../context/AuthContext'
import { api, formatDate } from '../lib/api'
import { hasFullControl } from '../lib/permissions'
import type { SystemStatus } from '../types'

export function ClusterPage() {
  const { session } = useAuth()
  const canSync = hasFullControl(session?.role)
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [error, setError] = useState('')
  const [syncing, setSyncing] = useState(false)
  const load = useCallback(() => { setError(''); api<SystemStatus>('/status').then(setStatus).catch(caught => setError(caught.message)) }, [])
  useEffect(load, [load])
  const sync = async () => {
    setSyncing(true); setError('')
    try { await api('/sync', { method: 'POST' }); load() }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'No se pudo iniciar la sincronización') }
    finally { setSyncing(false) }
  }
  if (error && !status) return <ErrorState message={error} retry={load} />
  if (!status) return <LoadingState />
  return <><PageHeader eyebrow="ADMINISTRACIÓN" title="Nodos y alta disponibilidad" description="Estado operativo del nodo local, replicación documental y proyección Git." actions={canSync && <button className="button primary" onClick={() => void sync()} disabled={syncing}><RefreshCw size={17} className={syncing ? 'spin' : ''} /> {syncing ? 'Sincronizando…' : 'Sincronizar ahora'}</button>} />{error && <ErrorState message={error} />}
    <div className="status-grid">
      <ContentCard className="status-card"><div className="status-card-icon active"><Server size={23} /></div><span>Rol del nodo</span><strong>{status.role === 'active' ? 'Activo' : status.role}</strong><small>{status.node}</small></ContentCard>
      <ContentCard className="status-card"><div className="status-card-icon"><Clock3 size={23} /></div><span>Intervalo</span><strong>{Math.round(status.sync_interval_seconds / 60)} minutos</strong><small>Sincronización automática</small></ContentCard>
      <ContentCard className="status-card"><div className="status-card-icon"><Database size={23} /></div><span>Reloj lógico</span><strong>{status.sync.clock}</strong><small>{status.sync.documents} entidades documentales</small></ContentCard>
      <ContentCard className="status-card"><div className="status-card-icon"><HardDrive size={23} /></div><span>Retención</span><strong>{status.retention_days} días</strong><small>Contenido del vault</small></ContentCard>
    </div>
    <div className="system-grid">
      <ContentCard><div className="card-heading"><div><span className="eyebrow">RÉPLICAS</span><h2>Estado de sincronización</h2></div><Network size={21} /></div><div className="peer-list">{status.peers_configured.length ? status.peers_configured.map(peer => { const value = status.sync.peers[peer]; return <div className="peer-row" key={peer}><span className={`peer-icon ${value?.ok ? 'ok' : 'unknown'}`}>{value?.ok ? <CheckCircle2 size={18} /> : <XCircle size={18} />}</span><div><strong>{peer}</strong><span>{value?.ok ? 'Última réplica correcta' : value?.error || 'Todavía no verificado'}</span></div><time>{formatDate(value?.at)}</time></div> }) : <p className="muted">No hay pares configurados.</p>}</div></ContentCard>
      <ContentCard><div className="card-heading"><div><span className="eyebrow">HISTORIAL</span><h2>Repositorio Git</h2></div><GitBranch size={21} /></div><div className="git-status"><span className={`large-status ${status.git.ready ? 'ok' : 'bad'}`}>{status.git.ready ? <ShieldCheck size={25} /> : <XCircle size={25} />}</span><div><strong>{status.git.ready ? 'Repositorio preparado' : 'Repositorio no disponible'}</strong><span>{status.git.clean ? 'Sin cambios pendientes' : status.git.error || 'Hay cambios por registrar'}</span></div></div>{status.git.head && <div className="commit-value"><span>Último commit</span><code>{status.git.head.slice(0, 12)}</code></div>}</ContentCard>
    </div>
  </>
}

export function SystemSettingsPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { api<SystemStatus>('/status').then(setStatus).catch(caught => setError(caught.message)) }, [])
  if (error) return <ErrorState message={error} />
  if (!status) return <LoadingState />
  return <><PageHeader eyebrow="AJUSTES" title="Configuración del sistema" description="Valores efectivos de esta instancia. Los cambios de infraestructura se realizan desde la plantilla de Unraid." />
    <ContentCard className="settings-list"><div className="settings-section"><div className="settings-icon"><Settings size={21} /></div><div><h2>Aplicación</h2><p>Identidad y comportamiento de la instancia.</p></div></div><dl className="configuration-table"><div><dt>Versión</dt><dd>{status.version}</dd></div><div><dt>Nodo</dt><dd>{status.node}</dd></div><div><dt>Rol efectivo</dt><dd>{status.role}</dd></div><div><dt>IP flotante</dt><dd>{status.floating_ip || 'No asignada'}</dd></div><div><dt>URL flotante</dt><dd>{status.floating_url || 'No configurada'}</dd></div></dl></ContentCard>
    <ContentCard className="settings-list"><div className="settings-section"><div className="settings-icon"><Network size={21} /></div><div><h2>Keepalived</h2><p>Reclamación autenticada de la dirección flotante.</p></div></div><dl className="configuration-table"><div><dt>Estado</dt><dd>{status.floating_ip_connector.state}</dd></div><div><dt>Origen</dt><dd>{status.floating_ip_connector.source || 'No configurado'}</dd></div><div><dt>Servicio</dt><dd>{status.floating_ip_connector.service}</dd></div><div><dt>Última confirmación</dt><dd>{formatDate(status.floating_ip_connector.last_success_at)}</dd></div>{status.floating_ip_connector.error && <div><dt>Error</dt><dd>{status.floating_ip_connector.error}</dd></div>}</dl></ContentCard>
    <ContentCard className="settings-list"><div className="settings-section"><div className="settings-icon"><ShieldCheck size={21} /></div><div><h2>Conservación y réplica</h2><p>Políticas aplicadas al contenido documental.</p></div></div><dl className="configuration-table"><div><dt>Retención del vault</dt><dd>{status.retention_days} días</dd></div><div><dt>Intervalo de sincronización</dt><dd>{status.sync_interval_seconds} segundos</dd></div><div><dt>Pares configurados</dt><dd>{status.peers_configured.join(', ') || 'Ninguno'}</dd></div><div><dt>Propietario de la VIP</dt><dd>{status.owns_floating_ip ? 'Sí' : 'No'}</dd></div></dl></ContentCard>
  </>
}
