import React from 'react';
import { Admin, Resource } from 'react-admin';
import customDataProvider from './customDataProvider';
import authProvider from './authProvider';
import ScoreRuleList from './ScoreRuleList';
import ScoreRuleCreate from './ScoreRuleCreate';


const App = () => (
    <Admin dataProvider={customDataProvider} authProvider={authProvider}>
        <Resource name="score_rules" list={ScoreRuleList} create={ScoreRuleCreate} />
    </Admin>
);

export default App;