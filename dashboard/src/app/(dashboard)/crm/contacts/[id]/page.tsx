'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Phone, Mail, MapPin, MessageSquare, Clock, Calendar, Briefcase, Zap } from 'lucide-react';

export default function ContactProfilePage() {
  const [contact, setContact] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const params = useParams();
  const contactId = params?.id as string;
  const router = useRouter();

  const getApiUrl = () => {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  };

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('agentego_token');
      // Buscar Contatos e Filtrar (Ideal: ter endpoint GET /contacts/:id)
      const resContact = await fetch(`${getApiUrl()}/api/crm/contacts/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const dataContacts = await resContact.json();
      const found = dataContacts.find((c: any) => c.id === contactId);
      if (found) setContact(found);

      // Buscar Atividades do Contato
      const resAct = await fetch(`${getApiUrl()}/api/crm/activities/?contact_id=${contactId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resAct.ok) {
        const dataAct = await resAct.json();
        setActivities(dataAct);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contactId) fetchData();
  }, [contactId]);

  if (loading) return <div className="p-8">Carregando Visão 360º...</div>;
  if (!contact) return <div className="p-8 text-red-500">Contato não encontrado.</div>;

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 pb-2 border-b border-[var(--color-border)]">
        <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500">
          <ArrowLeft size={20} />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{contact.name}</h2>
          <p className="text-sm text-gray-500">Visão 360º do Cliente</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coluna Esquerda: Dados do Cliente */}
        <div className="col-span-1 flex flex-col gap-6">
          
          {/* Card Resumo */}
          <div className="bg-white p-6 rounded-xl border border-[var(--color-border)] shadow-sm">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-[var(--color-brand-600)] to-[var(--color-brand-400)] flex items-center justify-center text-white text-2xl font-bold">
                {contact.name.charAt(0)}
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">{contact.name}</h3>
                <span className={`px-2 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full ${
                  contact.status === 'lead' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                }`}>
                  {contact.status}
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Phone size={16} className="text-gray-400" />
                <span>{contact.phone}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Mail size={16} className="text-gray-400" />
                <span>{contact.email || 'Não informado'}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Briefcase size={16} className="text-gray-400" />
                <span>Origem: {contact.source || 'Orgânico'}</span>
              </div>
            </div>
          </div>

          {/* Card Memória da IA (CrmContext) - Estático por enquanto */}
          <div className="bg-gradient-to-br from-indigo-50 to-white p-6 rounded-xl border border-indigo-100 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Zap size={18} className="text-indigo-600" />
              <h3 className="font-bold text-indigo-900">Memória da IA (Resumo)</h3>
            </div>
            <p className="text-sm text-indigo-900/80 leading-relaxed mb-4">
              Ainda não há interações recentes o suficiente para a IA gerar um resumo semanal para este cliente.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-md font-medium">Interesse: Médio</span>
            </div>
          </div>

        </div>

        {/* Coluna Direita: Timeline de Atividades */}
        <div className="col-span-1 lg:col-span-2">
          <div className="bg-white p-6 rounded-xl border border-[var(--color-border)] shadow-sm h-full">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold text-gray-900">Timeline de Atividades</h3>
              <button className="text-sm text-[var(--color-brand-600)] font-medium hover:underline">
                + Nova Nota
              </button>
            </div>

            {activities.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                  <Clock size={24} className="text-gray-400" />
                </div>
                <h4 className="font-medium text-gray-900">Nenhuma atividade registrada</h4>
                <p className="text-sm text-gray-500 mt-1 max-w-sm">
                  Crie notas, agende ligações ou deixe que a IA registre resumos de conversas importantes aqui.
                </p>
              </div>
            ) : (
              <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
                {activities.map((act) => (
                  <div key={act.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-[var(--color-brand-100)] text-[var(--color-brand-600)] shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                      <MessageSquare size={16} />
                    </div>
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-[var(--color-border)] bg-white shadow-sm">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-bold text-gray-900 text-sm">{act.subject}</span>
                        <span className="text-[10px] font-semibold text-gray-500 uppercase">
                          {new Date(act.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{act.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
