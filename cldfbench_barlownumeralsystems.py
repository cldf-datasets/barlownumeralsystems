import pathlib
import re

from cldfbench import CLDFSpec, Dataset as BaseDataset
from pybtex.database import parse_string


def normalise(id_):
    id_ = id_.replace(' ', '-')
    return id_


def clean_sources(sources_field):
    sources = (s.strip() for s in sources_field.split(','))
    return [re.sub(r'\s*\([^)]*\)', '', s) for s in sources if s]


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "barlownumeralsystems"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(
            dir=self.cldf_dir,
            module="StructureDataset",
            metadata_fname='cldf-metadata.json')

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        pass

    def cmd_readme(self, args):
        section_header = (
            'Barlow 2023 on Austronesian and Papuan numeral systems\n'
            '======================================================\n'
            '\n')
        section_content = self.raw_dir.read('intro.md')
        return f'{section_header}\n{section_content}'

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.

        >>> args.writer.objects['LanguageTable'].append(...)
        """
        raw_data = (
            {k.strip(): v.strip()
             for k, v in row.items()
             if v.strip() and v.strip() != '_'}
            for row in self.raw_dir.read_csv(
                'barlow-austronesian-papuan-numeral-systems.csv', dicts=True))
        raw_data = [row for row in raw_data if row]

        parameter_table = list(
            self.etc_dir.read_csv('parameters.csv', dicts=True))
        code_table = {
            (row['Parameter_ID'], row['Original_Name']): row
            for row in self.etc_dir.read_csv('codes.csv', dicts=True)}

        sources = parse_string(self.raw_dir.read('sources.bib'), 'bibtex')

        language_sources = {
            row['Glottocode']: clean_sources(row.get('Datasets') or '')
            for row in raw_data}

        glottocodes = {row['Glottocode'] for row in raw_data}
        language_table = [
            {
                'ID': lang.id,
                'Name': lang.name,
                'Macroarea': lang.macroareas[0].name if lang.macroareas else '',
                'Latitude': lang.latitude,
                'Longitude': lang.longitude,
                'Glottocode': lang.id,
                'ISO639P3code': lang.iso,
                'Source': language_sources[lang.id],
            }
            for lang in args.glottolog.api.languoids(ids=glottocodes)]
        language_table.sort(key=lambda lang: lang['ID'])

        for parameter in parameter_table:
            if parameter.get('Closed_Value_Set') == 'yes':
                possible_values = {
                    value
                    for row in raw_data
                    if (value := row.get(parameter['Original_Name']))}
                code_table.update(
                    ((parameter['ID'], value),
                     {'ID': '{}-{}'.format(parameter['ID'], normalise(value)),
                      'Parameter_ID': parameter['ID'],
                      'Name': value})
                    for value in sorted(possible_values))

        value_table = [
            {
                'ID': '{}-{}'.format(row['Glottocode'], parameter['ID']),
                'Language_ID': row['Glottocode'],
                'Parameter_ID': parameter['ID'],
                'Comment':
                    row.get('Notes', '')
                    if parameter['ID'] in {'numeral-system', 'numeral-subsystem'}
                    else '',
                'Code_ID':
                    code_table
                    .get((parameter['ID'], value), {})
                    .get('ID', ''),
                'Value': value,
            }
            for row in raw_data
            for parameter in parameter_table
            if (value := row.get(parameter['Original_Name']))]

        args.writer.cldf.add_component(
            'LanguageTable',
            'http://cldf.clld.org/v1.0/terms.rdf#source')
        args.writer.cldf.add_component('ParameterTable')
        args.writer.cldf.add_component('CodeTable', 'Map_Icon')

        args.writer.objects['LanguageTable'] = language_table
        args.writer.objects['ParameterTable'] = parameter_table
        args.writer.objects['CodeTable'] = code_table.values()
        args.writer.objects['ValueTable'] = value_table

        args.writer.cldf.add_sources(sources)
