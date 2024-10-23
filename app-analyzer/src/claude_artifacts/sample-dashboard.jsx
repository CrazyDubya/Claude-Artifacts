// src/claude_artifacts/sample-dashboard.jsx
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { month: 'Jan', value: 1200 },
  { month: 'Feb', value: 1900 },
  { month: 'Mar', value: 1500 },
  { month: 'Apr', value: 2400 },
  { month: 'May', value: 2100 },
];

const SampleDashboard = () => {
  const [showData, setShowData] = useState(true);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Sample Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            className="mb-4"
            onClick={() => setShowData(!showData)}
          >
            {showData ? 'Hide' : 'Show'} Data
          </Button>

          {showData && (
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.map((item) => (
          <Card key={item.month}>
            <CardHeader>
              <CardTitle className="text-lg">{item.month}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default SampleDashboard;