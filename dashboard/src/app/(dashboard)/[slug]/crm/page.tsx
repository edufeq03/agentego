'use client';
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { DndContext, DragOverlay, closestCorners, KeyboardSensor, PointerSensor, useSensor, useSensors, DragStartEvent, DragEndEvent, useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Phone, Bot } from 'lucide-react';

const STAGES = [
  { id: 'new', title: 'Novos Leads' },
  { id: 'contact', title: 'Contato' },
  { id: 'proposal', title: 'Proposta' },
  { id: 'negotiation', title: 'Negociação' },
  { id: 'won', title: 'Ganho' }
];

function DroppableColumn({ id, children }: { id: string, children: React.ReactNode }) {
  const { setNodeRef } = useDroppable({ id });
  return (
    <div ref={setNodeRef} className="p-3 flex-1 overflow-y-auto min-h-[150px]">
      {children}
    </div>
  );
}

function SortableDealCard({ deal }: { deal: any }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: deal.id, data: deal });
  
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div 
      ref={setNodeRef} 
      style={style} 
      {...attributes} 
      {...listeners}
      className="bg-[var(--color-background)] p-4 rounded-lg shadow-sm border border-[var(--color-border)] cursor-grab active:cursor-grabbing mb-3 hover:border-[var(--color-brand-400)] transition-colors"
    >
      <h4 className="font-medium text-[var(--color-foreground)] text-sm mb-1">{deal.title}</h4>
      
      {deal.phone && (
        <div className="flex items-center text-xs text-gray-400 mb-2">
          <Phone className="w-3 h-3 mr-1" />
          <span>{deal.phone}</span>
        </div>
      )}
      
      <div className="flex items-center justify-between mb-2">
        <p className="text-[var(--color-foreground-muted)] text-xs font-semibold">
          R$ {deal.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
        </p>
        
        {deal.intent && (
          <span className="bg-[var(--color-brand-900)] text-[var(--color-brand-100)] text-[10px] px-2 py-0.5 rounded-full font-medium border border-[var(--color-brand-700)] truncate max-w-[100px]">
            {deal.intent}
          </span>
        )}
      </div>

      {deal.summary && (
        <div className="mt-3 pt-2 border-t border-[var(--color-border)]">
          <div className="flex items-start">
            <Bot className="w-3 h-3 mr-1 mt-0.5 text-gray-400 flex-shrink-0" />
            <p className="text-[var(--color-foreground-muted)] text-[11px] leading-tight line-clamp-2" title={deal.summary}>
              {deal.summary}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CRMPage() {
  const [deals, setDeals] = useState<any[]>([]);
  const [activeDeal, setActiveDeal] = useState<any | null>(null);
  const [error, setError] = useState('');
  const router = useRouter();
  const params = useParams();

  const getApiUrl = () => {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  };

  const fetchDeals = () => {
    const token = localStorage.getItem('agentego_token') || localStorage.getItem('token');
    fetch(`${getApiUrl()}/api/crm/deals/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => {
      if (res.status === 401) throw new Error('Unauthorized');
      return res.json();
    })
    .then(data => setDeals(data))
    .catch(() => {
      setError("Erro ao carregar dados do CRM.");
    });
  };

  useEffect(() => {
    fetchDeals();
  }, [router]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor)
  );

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const deal = deals.find(d => d.id === active.id);
    if (deal) setActiveDeal(deal);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveDeal(null);
    const { active, over } = event;
    
    if (!over) return;

    const dealId = active.id;
    let newStage = over.id as string;
    
    if (!STAGES.find(s => s.id === over.id)) {
      const overDeal = deals.find(d => d.id === over.id);
      if (overDeal) {
        newStage = overDeal.stage_id;
      }
    }

    const activeDealData = deals.find(d => d.id === dealId);
    if (!activeDealData || activeDealData.stage_id === newStage) return;

    // Optimistic update
    const previousDeals = [...deals];
    setDeals(deals.map(d => d.id === dealId ? { ...d, stage_id: newStage } : d));

    const token = localStorage.getItem('agentego_token') || localStorage.getItem('token');
    try {
      const res = await fetch(`${getApiUrl()}/api/crm/deals/${dealId}/stage`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ stage_id: newStage })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Erro ao mover negócio');
      }
      
      setError(''); // clean error
    } catch (err: any) {
      // Revert on error
      setDeals(previousDeals);
      setError(err.message);
      setTimeout(() => setError(''), 5000);
    }
  };

  return (
    <div className="flex-1 w-full flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-transparent p-6">
      <div className="mb-6 flex flex-col gap-4">
        <div className="flex justify-between items-end">
          <div>
            <div className="flex gap-4 mb-2">
              <a href={`/${params?.slug || ''}/crm`} className="text-sm font-bold text-[var(--color-brand-500)] border-b-2 border-[var(--color-brand-500)] pb-1">Kanban</a>
              <a href={`/${params?.slug || ''}/crm/contacts`} className="text-sm font-medium text-[var(--color-foreground-muted)] hover:text-white pb-1">Contatos (360)</a>
            </div>
            <h2 className="text-2xl font-bold text-[var(--color-foreground)]">CRM de Vendas</h2>
            <p className="mt-1 text-sm text-[var(--color-foreground-muted)]">Acompanhe e movimente seus negócios ativos (Comercial OS).</p>
          </div>
          <button className="bg-[var(--color-brand-600)] text-white px-4 py-2 rounded-md shadow-sm hover:bg-[var(--color-brand-500)] transition-colors font-medium text-sm">
            + Novo Negócio
          </button>
        </div>
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded shadow-sm">
            <p className="text-sm text-red-700 font-medium">⚠️ {error}</p>
          </div>
        )}
      </div>

      <div className="flex gap-6 overflow-x-auto overflow-y-hidden flex-1 pb-4">
        <DndContext 
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          {STAGES.map(stage => {
            const stageDeals = deals.filter(d => d.stage_id === stage.id);
            
            return (
              <div key={stage.id} className="flex-shrink-0 w-80 flex flex-col bg-[var(--color-surface)] rounded-xl h-full border border-[var(--color-border)]">
                <div className="p-4 flex justify-between items-center border-b border-[var(--color-border)] bg-[var(--color-surface)] rounded-t-xl">
                  <h3 className="font-semibold text-[var(--color-foreground)]">{stage.title}</h3>
                  <span className="bg-[var(--color-surface-hover)] text-[var(--color-foreground-muted)] text-xs font-bold px-2 py-1 rounded-full">{stageDeals.length}</span>
                </div>
                
                <DroppableColumn id={stage.id}>
                  <SortableContext 
                    id={stage.id}
                    items={stageDeals.map(d => d.id)}
                    strategy={verticalListSortingStrategy}
                  >
                    {stageDeals.map(deal => (
                      <SortableDealCard key={deal.id} deal={deal} />
                    ))}
                  </SortableContext>
                  
                  {stageDeals.length === 0 && (
                    <div className="h-24 rounded-lg border-2 border-dashed border-[var(--color-border)] flex items-center justify-center text-[var(--color-foreground-muted)] text-sm font-medium">
                      Arraste para cá
                    </div>
                  )}
                </DroppableColumn>
              </div>
            );
          })}
          
          <DragOverlay>
            {activeDeal ? (
              <div className="bg-[var(--color-background)] p-4 rounded-lg shadow-xl border-2 border-[var(--color-brand-400)] opacity-90 rotate-2">
                <h4 className="font-medium text-[var(--color-foreground)] text-sm mb-1">{activeDeal.title}</h4>
                <p className="text-[var(--color-foreground-muted)] text-xs font-semibold">
                  R$ {activeDeal.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </p>
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </div>
    </div>
  );
}
