"use client";

import { useEffect, useState } from "react";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/api/summary")
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">{data?.summary?.title}</h1>
      <p className="text-gray-600 mb-8">{data?.summary?.overview}</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-sm font-medium text-gray-500">Commits</h3>
          <p className="text-2xl font-bold">{data?.summary?.metrics?.commits}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-sm font-medium text-gray-500">Pull Requests</h3>
          <p className="text-2xl font-bold">{data?.summary?.metrics?.pull_requests}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-sm font-medium text-gray-500">Issues Closed</h3>
          <p className="text-2xl font-bold">{data?.summary?.metrics?.issues_closed}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="font-medium mb-2">Completed Tasks</h3>
          <ul className="list-disc pl-5">
            {data?.summary?.completed_tasks?.map((task, i) => (
              <li key={i} className="text-sm">{task}</li>
            ))}
          </ul>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="font-medium mb-2">Pending Tasks</h3>
          <ul className="list-disc pl-5">
            {data?.summary?.pending_tasks?.map((task, i) => (
              <li key={i} className="text-sm">{task}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}