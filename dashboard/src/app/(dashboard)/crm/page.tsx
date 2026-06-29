'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DndContext, DragOverlay, closestCorners, KeyboardSensor, PointerSensor, useSensor, useSensors, DragStartEvent, DragEndEvent, useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

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
      className="bg-white p-4 rounded-lg shadow border border-gray-200 cursor-grab active:cursor-grabbing mb-3 hover:border-blue-300 transition-colors"
    >
      <h4 className="font-medium text-gray-900 text-sm mb-1">{deal.title}</h4>
      <p className="text-gray-500 text-xs font-semibold">
        R$ {deal.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
      </p>
    </div>
  );
}

export default function CRMPage() {
  const [deals, setDeals] = useState<any[]>([]);
  const [activeDeal, setActiveDeal] = useState<any | null>(null);
  const [error, setError] = useState('');
  const router = useRouter();

  const getApiUrl = () => {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  };

  const fetchDeals = () => {
    const token = localStorage.getItem('token');
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

    const token = localStorage.getItem('token');
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
    <div className="flex-1 w-full flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-gray-50 p-6">
      <div className="mb-6 flex flex-col gap-4">
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">CRM de Vendas</h2>
            <p className="mt-1 text-sm text-gray-600">Acompanhe e movimente seus negócios ativos (Comercial OS).</p>
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md shadow-sm hover:bg-blue-700 transition-colors font-medium text-sm">
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
              <div key={stage.id} className="flex-shrink-0 w-80 flex flex-col bg-gray-100 rounded-xl h-full border border-gray-200">
                <div className="p-4 flex justify-between items-center border-b border-gray-200 bg-gray-50/50 rounded-t-xl">
                  <h3 className="font-semibold text-gray-700">{stage.title}</h3>
                  <span className="bg-gray-200 text-gray-600 text-xs font-bold px-2 py-1 rounded-full">{stageDeals.length}</span>
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
                    <div className="h-24 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-400 text-sm font-medium">
                      Arraste para cá
                    </div>
                  )}
                </DroppableColumn>
              </div>
            );
          })}
          
          <DragOverlay>
            {activeDeal ? (
              <div className="bg-white p-4 rounded-lg shadow-xl border-2 border-blue-400 opacity-90 rotate-2">
                <h4 className="font-medium text-gray-900 text-sm mb-1">{activeDeal.title}</h4>
                <p className="text-gray-500 text-xs font-semibold">
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
