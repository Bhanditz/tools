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
package eu.annocultor.tagger.vocabularies;

import java.io.File;
import java.util.Collection;

import eu.annocultor.common.Language.Lang;
import eu.annocultor.tagger.postprocessors.AdminDivisionTermFilter;
import eu.annocultor.tagger.postprocessors.PopulationTermFilter;
import eu.annocultor.tagger.terms.CodeURI;
import eu.annocultor.tagger.terms.Term;
import eu.annocultor.tagger.terms.TermList;


/**
 * Vocabulary of geographical places with its specific disambiguation context.
 * 
 * @author Borys Omelayenko
 * 
 */
public class VocabularyOfPlaces extends AbstractVocabulary
{
	public static enum PLACE_TYPES
	{
		city(
				"city"),
		country(
				"country");

		String label;

		PLACE_TYPES(String label)
		{
			this.label = label;
		}
	}

	VocabularyOfTerms placeTypes = new VocabularyOfTerms("placeTypes", Lang.en);

	public TermList lookupPlace(String place, Collection<PLACE_TYPES> placeTypes, Collection<CodeURI> parent)
			throws Exception
	{
		// get all terms this label
		TermList termList = findByLabel(place, new DisambiguationContext(null, Lang.en, parent));
		return termList;
		
//		// TODO - create dismbiguator , use getUnambigous()
//		if (termList.isEmpty())
//			return null;
//
//		// find matching place types
//		List<Term> result = new ArrayList<Term>();
//		for (Term term : termList)
//		{
//			if (placeTypes != null)
//			{
//				// for (PLACE_TYPES placeType : placeTypes)
//				// {
//				//
//				// }
//			}
//			else
//			{
//				result.add(term);
//			}
//		}
//
//		if (result.size() != 1)
//		{
//			return null;
//		}
//		return result.get(0);
	}

	@Override
	public void loadTermPropertiesSPARQL(String propertyName, String query, File cacheDir, File dir, String... files)
			throws Exception
	{
		// load vocabulary of property values
		VocabularyOfTerms attributeVocabulary = new VocabularyOfTerms(name + "_A_" + propertyName, null);
		attributeVocabulary.clearDisambiguators();
		
		attributeVocabulary.loadTermsSPARQL(query, cacheDir, dir, files);

		// apply property values to loaded terms
		for (TermList terms : listAllByCode())
		{
			for (Term term : terms)
			{
				TermList propertyTerms = attributeVocabulary.findByCode(new CodeURI(term.getCode()));
				for (Term propertyTerm : propertyTerms)
				{
					term.setProperty(propertyName, propertyTerm.getLabel());
				}
			}
		}

	}

	public VocabularyOfPlaces(String name, Lang lang)
	{
		super(name, lang);
		addDisambiguator(new PopulationTermFilter());
		addDisambiguator(new AdminDivisionTermFilter());
	}

}
