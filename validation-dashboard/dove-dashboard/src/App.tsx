import { useState } from 'react';
import dashboardData from './data/dashboard-data.json';
import validationData from './data/individual-validation-data.json';
import extendedAggData from './data/extended-aggregate-data.json';
import extendedValData from './data/extended-validation-data.json';
import { DashboardHeader } from './components/layout/DashboardHeader';
import { AggregateTab } from './components/aggregate/AggregateTab';
import { IndividualValidationTab } from './components/individual/IndividualValidationTab';
import { ExtendedAggregateTab } from './components/extended-aggregate/ExtendedAggregateTab';
import { ExtendedValidationTab } from './components/extended-validation/ExtendedValidationTab';
import type { DashboardData, DashboardTab } from './types';
import type { IndividualValidationData } from './types/individual';
import type { ExtendedValidationData } from './types/extended';

const data = dashboardData as unknown as DashboardData;
const individualData = validationData as unknown as IndividualValidationData;
const extAggData = extendedAggData as unknown as DashboardData;
const extValData = extendedValData as unknown as ExtendedValidationData;

function App() {
  const [activeTab, setActiveTab] = useState<DashboardTab>('aggregate');

  return (
    <div className="min-h-screen bg-darpan-bg">
      <DashboardHeader
        data={data}
        extData={extAggData}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      <main>
        {activeTab === 'aggregate' ? (
          <AggregateTab data={data} />
        ) : activeTab === 'individual' ? (
          <IndividualValidationTab data={individualData} />
        ) : activeTab === 'extended-aggregate' ? (
          <div className="max-w-[1400px] mx-auto">
            <ExtendedAggregateTab data={extAggData} originalData={data} />
          </div>
        ) : (
          <div className="max-w-[1400px] mx-auto">
            <ExtendedValidationTab data={extValData} baselineData={individualData} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
