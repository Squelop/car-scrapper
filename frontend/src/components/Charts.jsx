import React, { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, LineChart, Line, Legend } from 'recharts'

const Charts = ({ listings }) => {

    const priceByYear = useMemo(() => {
        if (!listings.length) return [];

        const grouped = listings.reduce((acc, curr) => {
            if (!curr.production_year || !curr.price) return acc;
            if (!acc[curr.production_year]) {
                acc[curr.production_year] = { year: curr.production_year, total: 0, count: 0 }
            }
            acc[curr.production_year].total += curr.price;
            acc[curr.production_year].count += 1;
            return acc;
        }, {})

        return Object.values(grouped)
            .map(g => ({ ...g, avgPrice: Math.round(g.total / g.count) }))
            .sort((a, b) => a.year - b.year)
    }, [listings])

    // Historical price tracking (by scraped_at date)
    const priceOverTime = useMemo(() => {
        if (!listings.length) return [];

        const grouped = listings.reduce((acc, curr) => {
            if (!curr.scraped_at || !curr.price) return acc;

            // Extract date (YYYY-MM-DD)
            const date = curr.scraped_at.split('T')[0];

            if (!acc[date]) {
                acc[date] = { date, total: 0, count: 0 }
            }
            acc[date].total += curr.price;
            acc[date].count += 1;
            return acc;
        }, {})

        return Object.values(grouped)
            .map(g => ({ ...g, avgPrice: Math.round(g.total / g.count) }))
            .sort((a, b) => a.date.localeCompare(b.date))
    }, [listings])

    // Price by fuel type
    const priceByFuel = useMemo(() => {
        if (!listings.length) return [];

        const grouped = listings.reduce((acc, curr) => {
            if (!curr.fuel_type || !curr.price) return acc;

            if (!acc[curr.fuel_type]) {
                acc[curr.fuel_type] = { fuel: curr.fuel_type, total: 0, count: 0 }
            }
            acc[curr.fuel_type].total += curr.price;
            acc[curr.fuel_type].count += 1;
            return acc;
        }, {})

        return Object.values(grouped)
            .map(g => ({ ...g, avgPrice: Math.round(g.total / g.count) }))
            .sort((a, b) => b.avgPrice - a.avgPrice)
    }, [listings])

    return (
        <>
            {/* Historical Price Trend */}
            {priceOverTime.length > 1 && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 lg:col-span-2">
                    <h3 className="text-lg font-semibold mb-4 text-slate-800">Average Price Over Time</h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={priceOverTime}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                <XAxis dataKey="date" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value / 1000}k`} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    cursor={{ stroke: '#3B82F6', strokeWidth: 1 }}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="avgPrice" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} name="Avg Price (PLN)" />
                                <Line type="monotone" dataKey="count" stroke="#10B981" strokeWidth={2} dot={{ r: 4 }} name="Listings Count" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold mb-4 text-slate-800">Average Price by Year</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={priceByYear}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                            <XAxis dataKey="year" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value / 1000}k`} />
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                cursor={{ fill: '#F1F5F9' }}
                            />
                            <Bar dataKey="avgPrice" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold mb-4 text-slate-800">Price vs Mileage</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                            <XAxis type="number" dataKey="mileage" name="Mileage" unit="km" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis type="number" dataKey="price" name="Price" unit="PLN" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value / 1000}k`} />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                            <Scatter name="Listings" data={listings} fill="#8B5CF6" fillOpacity={0.6} />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Price by Fuel Type */}
            {priceByFuel.length > 0 && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold mb-4 text-slate-800">Average Price by Fuel Type</h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={priceByFuel} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                                <XAxis type="number" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value / 1000}k`} />
                                <YAxis type="category" dataKey="fuel" fontSize={12} tickLine={false} axisLine={false} width={80} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Bar dataKey="avgPrice" fill="#10B981" radius={[0, 4, 4, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
        </>
    )
}

export default Charts
