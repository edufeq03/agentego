'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';

export default function ContactsListPage() {
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const params = useParams();

  const getApiUrl = () => {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  };

  const fetchContacts = async () => {
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('agentego_token');
      const res = await fetch(`${getApiUrl()}/api/crm/contacts/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Erro ao buscar contatos');
      const data = await res.json();
      setContacts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  return (
    <div className="flex-1 w-full bg-white rounded-xl shadow-sm border border-[var(--color-border)] overflow-hidden">
      <div className="p-6 border-b border-[var(--color-border)] flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Meus Contatos</h2>
          <p className="text-sm text-gray-500 mt-1">Lista de leads qualificados capturados pelo Comercial OS.</p>
        </div>
        <div className="flex gap-3">
          <Link href={`/${params?.slug || ''}/crm`} className="px-4 py-2 bg-gray-100 text-gray-700 font-medium text-sm rounded-lg hover:bg-gray-200 transition-colors">
            Voltar ao Kanban
          </Link>
          <button className="px-4 py-2 bg-[var(--color-brand-500)] text-white font-medium text-sm rounded-lg hover:bg-[var(--color-brand-600)] transition-colors">
            + Novo Contato
          </button>
        </div>
      </div>
      
      {loading ? (
        <div className="p-8 text-center text-gray-500">Carregando contatos...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-[var(--color-border)]">
                <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Nome</th>
                <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Telefone</th>
                <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Última Atualização</th>
                <th className="p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {contacts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    Nenhum contato encontrado. Importe leads para começar!
                  </td>
                </tr>
              ) : (
                contacts.map(contact => (
                  <tr key={contact.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="p-4 font-medium text-gray-900">{contact.first_name} {contact.last_name}</td>
                    <td className="p-4 text-gray-600">{contact.phone}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-xs font-bold rounded-full ${
                        contact.status === 'lead' ? 'bg-yellow-100 text-yellow-800' :
                        contact.status === 'client' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {contact.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-4 text-gray-500 text-sm">
                      {new Date(contact.updated_at).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="p-4 text-right">
                      <Link 
                        href={`/${params?.slug || ''}/crm/contacts/${contact.id}`}
                        className="text-[var(--color-brand-600)] hover:text-[var(--color-brand-800)] text-sm font-medium"
                      >
                        Ver Perfil
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
