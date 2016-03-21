Autocomplete suggestions with Solr
..................................

http://wiki.apache.org/solr/Suggester

Simple autocomplete configuration using the "Title" field (buildout.cfg)::

    additional-solrconfig =
      <searchComponent name="suggest" class="solr.SpellCheckComponent">
        <lst name="spellchecker">
          <str name="name">suggest</str>
          <str name="classname">org.apache.solr.spelling.suggest.Suggester</str>
          <str name="lookupImpl">org.apache.solr.spelling.suggest.fst.WFSTLookupFactory</str>
          <str name="field">Title</str>
          <float name="threshold">0.005</float>
          <str name="buildOnCommit">true</str>
        </lst>
      </searchComponent>

      <requestHandler name="/autocomplete" class="org.apache.solr.handler.component.SearchHandler">
         <lst name="defaults">
          <str name="spellcheck">true</str>
          <str name="spellcheck.dictionary">suggest</str>
          <str name="spellcheck.count">10</str>
          <str name="spellcheck.onlyMorePopular">true</str>
         </lst>
         <arr name="components">
          <str>suggest</str>
         </arr>
      </requestHandler>


More complex example with custom field/filters::

    index +=
        name:title_autocomplete type:text_auto indexed:true stored:true

    additional-solrconfig =
      <searchComponent name="suggest" class="solr.SpellCheckComponent">
        <lst name="spellchecker">
          <str name="name">suggest</str>
          <str name="classname">org.apache.solr.spelling.suggest.Suggester</str>
          <str name="lookupImpl">org.apache.solr.spelling.suggest.fst.WFSTLookupFactory</str>
          <str name="field">title_autocomplete</str>
          <float name="threshold">0.005</float>
          <str name="buildOnCommit">true</str>
        </lst>
      </searchComponent>

      <requestHandler name="/autocomplete" class="org.apache.solr.handler.component.SearchHandler">
         <lst name="defaults">
          <str name="spellcheck">true</str>
          <str name="spellcheck.dictionary">suggest</str>
          <str name="spellcheck.count">10</str>
          <str name="spellcheck.onlyMorePopular">true</str>
         </lst>
         <arr name="components">
          <str>suggest</str>
         </arr>
      </requestHandler>

    extra-field-types =
      <fieldType class="solr.TextField" name="text_auto">
        <analyzer>
          <tokenizer class="solr.WhitespaceTokenizerFactory"/>
          <filter class="solr.ShingleFilterFactory" maxShingleSize="4" outputUnigrams="true"/>
        </analyzer>
      </fieldType>

    additional-schema-config =
      <copyField source="Title" dest="title_autocomplete" />
