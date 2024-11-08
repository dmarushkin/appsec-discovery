import React from 'react';
import { Create, SimpleForm, TextInput, NumberInput, SelectInput } from 'react-admin';

const choices = [
    { id: 'active', name: 'Active' },
    { id: 'skip', name: 'Skip' },
 ];

const ScoreRuleCreate = (props) => (
    <Create {...props}>
        <SimpleForm>
            <TextInput source="service_re" />
            <TextInput source="object_re" />
            <TextInput source="object_type_re" />
            <TextInput source="field_re" />
            <TextInput source="field_type_re" />
            <NumberInput source="risk_score" />
            <SelectInput source="status" choices={choices}/>
        </SimpleForm>
    </Create>
);

export default ScoreRuleCreate;