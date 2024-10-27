import React from 'react';
import { List, Datagrid, TextField, NumberField, SelectField, DeleteButton, TopToolbar, CreateButton } from 'react-admin';

const ScoreRuleListActions = ({ basePath }) => (
    <TopToolbar>
        <CreateButton basePath={basePath} />
    </TopToolbar>
);

const ScoreRuleList = (props) => (
    <List actions={<ScoreRuleListActions />} {...props}>
        <Datagrid>
            <TextField source="id" />
            <TextField source="service_re" />
            <TextField source="object_re" />
            <TextField source="object_type_re" />
            <TextField source="field_re" />
            <TextField source="field_type_re" />
            <NumberField source="risk_score" />
            <TextField source="status" />
            <DeleteButton />
        </Datagrid>
    </List>
);

export default ScoreRuleList;