/*
 * Copyright 2005-2009 the original author or authors.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *      http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package eu.annocultor.tagger.rules;

import java.util.ArrayList;
import java.util.List;

import eu.annocultor.annotations.AnnoCultor;
import eu.annocultor.common.Language.Lang;
import eu.annocultor.context.Concepts.RDF;
import eu.annocultor.context.Environment;
import eu.annocultor.context.Environment.PARAMETERS;
import eu.annocultor.context.Namespace;
import eu.annocultor.path.Path;
import eu.annocultor.tagger.terms.CodeURI;
import eu.annocultor.tagger.terms.Term;
import eu.annocultor.tagger.terms.TermList;
import eu.annocultor.tagger.vocabularies.Vocabulary;
import eu.annocultor.tagger.vocabularies.VocabularyOfPeople;
import eu.annocultor.triple.LiteralValue;
import eu.annocultor.triple.Property;
import eu.annocultor.triple.Triple;
import eu.annocultor.triple.Value;
import eu.annocultor.xconverter.api.DataObject;
import eu.annocultor.xconverter.api.Graph;


/**
 * Looks people up in external vocabularies.
 * Should be applied to a <code>srcPath</code> that stores person names.
 * 
 * @author Borys Omelayenko
 * 
 */
public class LookupPersonRule extends AbstractLookupRule
{
	protected List<VocabularyOfPeople> vocabularies = new ArrayList<VocabularyOfPeople>();

	protected void addVocabulary(VocabularyOfPeople v) throws Exception
	{
		if (v == null) {
			throw new Exception("NULL vocabulary passed.");
		}
		vocabularies.add(v);
	}

	@Override
	public String getAnalyticalRuleClass()
	{
		return "VocabularyOfPeople";
	}

	protected Path lifeDatePath;
	protected Path birthDatePath;
	protected Path deathDatePath;
	private Path lifePlacePath;
	private Path birthPlacePath;
	private Path deathPlacePath;

	/**
	 * Linking external vocabularies is done directly, without the creation of local proxy terms. 
	 * 
	 * @param srcPath
	 * @param dstProperty
	 * @param dstGraphLinks 
	 * @param dstGraphLiterals
	 * @param pathBirthPath
	 * @param pathDeathPath
	 * @param termSplitPattern regular expression that defines how to separate multiple term labels merged into a single string.
	 *    For example the following pattern (quotes excluded) "( *; *)|( *, *)" would split terms by semicolon or comma
	 * @param termsVocabulary
	 * @throws Exception
	 */
	@AnnoCultor.XConverter(include=true, affix = "noLocalTerms")
	public LookupPersonRule(
			@AnnoCultor.XConverter.sourceXMLPath Path srcPath,
			Property dstProperty,
			Graph dstGraphLiterals,
			Graph dstGraphLinks,
			Path birthPath,
			Path deathPath,
			Property termsProperty,
			String termsSignature,			 
			String termsSplitPattern,
			VocabularyOfPeople... termsVocabulary)
	throws Exception
	{
		this(
				srcPath,
				termsProperty,
				dstProperty,
				null,
				null, // no local terms - no ns
				birthPath,
				deathPath,
				termsSignature,
				termsSplitPattern,
				dstGraphLiterals,
				dstGraphLinks,
				termsVocabulary
		);
	}

	//@AnnoCultor.XConverter(include=true, affix = "dates")
	public LookupPersonRule(
			@AnnoCultor.XConverter.sourceXMLPath Path srcPath,
			Property dstPropertyRecordToTermIfFound,
			Property dstPropertyRecordToLiteralIfNotFound,
			Lang langNames,
			Namespace nsLocalTerms,
			Path pathBirthDate,
			Path pathDeathDate,
			String mapName,
			String termSplitPattern,
			Graph dstGraphLiterals,
			Graph dstGraphLinksRecordToTerm,
			VocabularyOfPeople... vocabularyOfPeople)
	throws Exception
	{
		this(
				dstPropertyRecordToTermIfFound, 
				dstPropertyRecordToLiteralIfNotFound,
				null,
				null,
				nsLocalTerms,
				null,
				pathBirthDate,
				pathDeathDate,
				null,
				null,
				null,
				mapName,
				termSplitPattern,
				dstGraphLiterals,
				dstGraphLinksRecordToTerm,
				null);

		if (mapName == null || mapName.contains("/"))
		{
			throw new Exception("NULL or / in category "
					+ mapName
					+ " that is not allowed as this category becomes a part of a filename.");
		}

		if (pathBirthDate == null)
		{
			throw new NullPointerException("NULL is not allowed as author birth date XML path, as it is required for vocabulary lookup");
		}

		if (pathDeathDate == null)
		{
			throw new NullPointerException("NULL is not allowed as author death date XML path, as it is required for vocabulary lookup");
		}

		for (VocabularyOfPeople vocabulary : vocabularyOfPeople)
		{
			addVocabulary(vocabulary);
		}

		setSourcePath(srcPath);
	}

	public LookupPersonRule(
			@AnnoCultor.XConverter.sourceXMLPath Path srcXmlPath,
			Property dstRdfPropertyRecordToTermIfFound,
			Property dstRdfPropertyRecordToLiteralIfNotFound,
			Lang langNames,
			Namespace namespaceLocalTerms,
			Path xmlPathLifeDate,
			Path xmlPathBirthDate,
			Path xmlPathDeathDate,
			Path xmlPathLifePlace,
			Path xmlPathBirthPlace,
			Path xmlPathDeathPlace,
			String mapFileNameKeyword,
			Graph dstRdfGraphTerms,
			Graph dstRdfGraphLinksRecordToTerm)
	{
		this(
				dstRdfPropertyRecordToTermIfFound, 
				dstRdfPropertyRecordToLiteralIfNotFound,
				null,
				null,
				namespaceLocalTerms,
				xmlPathLifeDate,
				xmlPathBirthDate,
				xmlPathDeathDate,
				xmlPathLifePlace,
				xmlPathBirthPlace,
				xmlPathDeathPlace,
				mapFileNameKeyword,
				DEFAULT_SPLIT_PATTERN,
				dstRdfGraphTerms,
				dstRdfGraphLinksRecordToTerm,
				null//new PersonTermCreator()
		);
	}

	/**
	 * Looks triple values up in an external vocabulary.
	 * 
	 * @param linkRecordToTerm
	 *          to create if mappings found
	 * @param linkRecordToLiteral
	 *          to create if no mapping is found
	 * @param passedReportCategory
	 *          report category
	 * @param mappedReportCategory
	 *          report category
	 * @param splitPattern
	 *          to split a triple <code>value</code> into terms to be mapped
	 *          separately. <code>null</code> sets the no-separation logic.
	 * @param target
	 */
	public LookupPersonRule(
			Property linkRecordToTerm,
			Property linkRecordToLiteral,
			Property labelOfLinkTermToVocabulary,
			Lang langLabelTermToVocabulary,
			Namespace termsNamespace,
			Path lifeDatePath,
			Path birthDatePath,
			Path deathDatePath,
			Path lifePlacePath,
			Path birthPlacePath,
			Path deathPlacePath,
			String linksSignature,
			String termsSplitPattern,
			Graph dstGraph,
			Graph linksGraph,
			TermCreator termCreator)
	{
		super(
				linkRecordToTerm,
				linkRecordToLiteral,
				labelOfLinkTermToVocabulary,
				langLabelTermToVocabulary,
				linksSignature,
				termsSplitPattern,
				dstGraph,
				linksGraph,
				termCreator, 
				termsNamespace == null ? null : new ProxyTermDefinition(termsNamespace, dstGraph, null));
		this.lifeDatePath = lifeDatePath;
		this.birthDatePath = birthDatePath;
		this.deathDatePath = deathDatePath;
		this.lifePlacePath = lifePlacePath;
		this.birthPlacePath = birthPlacePath;
		this.deathPlacePath = deathPlacePath;

		if (!(this.lifePlacePath == null && this.birthPlacePath == null && this.deathPlacePath == null))
			throw new RuntimeException("lifePlacePath, birthPlacePath, deathPlacePath are not implemented yet.");
	}

	@Override
	protected TermList getDisambiguatedTerms(DataObject dataObject, String label, Lang lang) throws Exception
	{
		if (label == null)
			throw new NullPointerException("Null label (artist name)");
		TermList result = new TermList();
		for (VocabularyOfPeople vocabulary : vocabularies)
		{
			try
			{
				TermList person =
					vocabulary.lookupPerson(label,
							lang,
							getFirstValueIfPathExists(dataObject, birthPlacePath), 
							getFirstValueIfPathExists(dataObject, deathDatePath), 
							getFirstValueIfPathExists(dataObject, lifeDatePath), 
							null,
							null,
							null,
							null);
				result.add(person);
			}
			catch (Exception e)
			{
				throw new Exception("Vocabulary lookup error on term '"
						+ label
						+ "', vocabulary "
						+ vocabulary.getVocabularyName()
						+ ": "
						+ e.getMessage());
			}
		}
		return result;
	}

	@Override
	public void fire(Triple triple, DataObject dataObject) throws Exception
	{
		try
		{
			Value name = triple.getValue();
			name = deQuote(name);

			super.fire(triple.changeValue(name), dataObject);

			//			String termUri = Common.generateNameBasedUri(proxyTermDefinition.namespaceLocalTerms, name);

			//			if (objectMap != null)
			//			{
			//				objectMap.processDataObject(termUri, dataObject);
			//			}

		}
		catch (Exception e)
		{
			throw new Exception("Person Writer error on triple " + triple, e);
		}
	}

    Value deQuote(Value name) {
        String value = name.getValue();
        if (value != null && value.length() > 2 && value.startsWith("\"") && value.endsWith("\""))
        	name = new LiteralValue(value.substring(1, value.length() - 1));
        return name;
    }

	@Override
	public TermList getTermsByUri(CodeURI uri) throws Exception {
		TermList terms = new TermList();
		for (Vocabulary vocabulary : vocabularies) {
			for (Term term : vocabulary.findByCode(uri)) {
				terms.add(term);
			}
		}
		return terms;
	}

	protected static class PersonTermCreator extends TermCreator
	{

		Environment environment;

		public PersonTermCreator(String scheme, LabelCaseOption makeLowCaseLabels, Environment environment)
		{
			// hope for late setObjectRule			
			super(scheme, makeLowCaseLabels);
			this.environment = environment;
		}

		protected PersonTermCreator(String scheme, TermCreatorInt tc)
		{
			super(scheme, tc);
		}

		@Override
		public String getTermType()
		{
			return environment.getParameter(PARAMETERS.ANNOCULTOR_MODEL_PERSON);
		}

		@Override
		public Property getRelationTermToVocabulary()
		{
			return RDF.SAMEAS;
		}

		@Override
		public Property getPrefLabelProperty()
		{
			return new Property(environment.getParameter(PARAMETERS.ANNOCULTOR_MODEL_PERSON_NAME));
		}

	}

}