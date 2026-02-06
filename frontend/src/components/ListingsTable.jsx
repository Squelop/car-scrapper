import React from 'react'

const ListingsTable = ({ listings }) => {
    if (!listings.length) {
        return <div className="p-8 text-center text-slate-500">No listings found yet. Start scraping to see data.</div>
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-600">
                <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500">
                    <tr>
                        <th className="px-6 py-4">Title</th>
                        <th className="px-6 py-4">Price</th>
                        <th className="px-6 py-4">Year</th>
                        <th className="px-6 py-4">Mileage</th>
                        <th className="px-6 py-4">Fuel</th>
                        <th className="px-6 py-4">Source</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {listings.map((item) => (
                        <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                            <td className="px-6 py-4 font-medium text-slate-900">
                                <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 hover:underline">
                                    {item.model || "Unknown Model"}
                                </a>
                            </td>
                            <td className="px-6 py-4 font-bold text-emerald-600">
                                {item.price?.toLocaleString()} {item.currency}
                            </td>
                            <td className="px-6 py-4">{item.production_year}</td>
                            <td className="px-6 py-4">
                                {item.mileage ? `${item.mileage.toLocaleString()} km` : '-'}
                            </td>
                            <td className="px-6 py-4">{item.fuel_type}</td>
                            <td className="px-6 py-4 text-xs text-slate-400 capitalize">{item.platform}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default ListingsTable
