"""
Generate a high-quality fake news dataset with realistic examples.
This creates news that has distinguishable patterns between fake and real.
"""
import csv
import random
from datetime import datetime, timedelta

OUTPUT_PATH = "fake_news_dataset.csv"

# ============================================================
# REAL NEWS TEMPLATES - Factual, neutral, professional tone
# ============================================================
REAL_NEWS_TEMPLATES = [
    # Politics / Government
    ("Senate passes bipartisan infrastructure bill with {num} votes",
     "The United States Senate voted {num} to approve the bipartisan infrastructure package on {date}. The bill includes funding for roads, bridges, broadband, and water systems. Supporters say it will create jobs and modernize aging infrastructure across the country."),
    ("President signs executive order on {topic}",
     "The President signed an executive order addressing {topic} during a ceremony at the White House. Officials said the order is aimed at improving federal response and coordination. The move was praised by some lawmakers while others called for congressional action instead."),
    ("Federal Reserve holds interest rates steady at current levels",
     "The Federal Reserve announced it would keep interest rates unchanged following its latest policy meeting. Chair stated that the economy continues to show resilience but inflation remains above target. Markets reacted calmly to the widely expected decision."),
    ("Supreme Court agrees to hear case on {topic}",
     "The Supreme Court announced it will hear arguments in a major case involving {topic}. Legal experts say the decision could have significant implications for federal policy. The case is expected to be argued during the next term."),
    ("Congress approves {amount} billion spending package",
     "The House and Senate approved a {amount} billion spending package to fund government operations. The legislation includes provisions for defense, healthcare, and education. The bill now heads to the President's desk for signature."),
    ("Governor announces plan to invest in {topic}",
     "The state governor unveiled a comprehensive plan to invest in {topic} over the next five years. The initiative is expected to create thousands of jobs and improve public services. Funding will come from a combination of state and federal sources."),
    ("City council votes to approve new public transit expansion",
     "The city council voted unanimously to approve a major expansion of the public transit system. The project will add new bus routes and light rail stations to underserved neighborhoods. Construction is expected to begin next year and be completed within three years."),
    ("Local election results certified after routine audit",
     "Election officials certified the results of the local election following a routine post-election audit. The audit confirmed the accuracy of the vote count with a margin of error below 0.1 percent. Officials said the process worked as intended and voter turnout was the highest in a decade."),

    # Economy / Business
    ("Stock market closes higher as tech sector leads gains",
     "Major stock indexes closed higher on {date} as technology stocks led the rally. The S&P 500 rose 1.2 percent while the Nasdaq gained 1.8 percent. Analysts attributed the gains to strong earnings reports from several major tech companies."),
    ("Unemployment rate drops to {num} percent in latest report",
     "The Bureau of Labor Statistics reported that unemployment fell to {num} percent last month. The economy added approximately 250,000 new jobs, exceeding analyst expectations. Job growth was strongest in healthcare, technology, and construction sectors."),
    ("{company} reports quarterly earnings above expectations",
     "{company} released its quarterly financial results showing revenue of {amount} billion dollars. The company exceeded analyst expectations for both revenue and profit. CEO cited strong consumer demand and operational efficiency as key drivers."),
    ("Global trade volume increases by {num} percent year over year",
     "International trade volumes rose {num} percent compared to the same period last year according to the World Trade Organization. The growth was driven by strong demand in Asia and recovering European markets. Trade officials noted that supply chain improvements contributed to the positive trend."),
    ("New housing starts reach highest level in {num} years",
     "The Commerce Department reported that new housing construction starts reached their highest level in {num} years. Single-family home construction led the increase, rising 8 percent from the previous month. Analysts say the trend reflects strong demand and improving builder confidence."),
    ("Central bank announces gradual tapering of bond purchases",
     "The central bank announced it will begin gradually reducing its bond-buying program starting next month. The move signals growing confidence in the economic recovery. Officials emphasized that interest rate increases remain separate from the tapering decision."),

    # Science / Technology
    ("NASA successfully launches new Earth observation satellite",
     "NASA launched a new Earth observation satellite from Cape Canaveral on {date}. The satellite will monitor climate patterns, sea levels, and atmospheric changes. Scientists say the data will improve weather forecasting and climate research."),
    ("Researchers develop new treatment showing promise for {topic}",
     "A team of researchers at a leading university has developed a new treatment approach for {topic}. Early clinical trials show positive results with manageable side effects. The researchers emphasized that larger trials are needed before the treatment can be widely available."),
    ("New study finds link between exercise and reduced risk of {topic}",
     "A peer-reviewed study published in a medical journal found that regular exercise is associated with a reduced risk of {topic}. The research followed over 10,000 participants for five years. Authors noted that the findings support existing public health recommendations for physical activity."),
    ("Tech company unveils new {product} at annual conference",
     "A major technology company unveiled its latest {product} at its annual developer conference. The device features improved performance, longer battery life, and new software capabilities. Industry analysts say it represents an incremental but meaningful upgrade over previous models."),
    ("International Space Station crew completes scheduled {topic} experiment",
     "Astronauts aboard the International Space Station completed a series of experiments related to {topic}. The research was conducted over three weeks and produced preliminary data that will be analyzed on Earth. NASA officials said the experiments went as planned."),
    ("Climate scientists publish updated projections in peer-reviewed journal",
     "An international team of climate scientists published updated climate projections in a leading peer-reviewed journal. The study used improved modeling techniques and decades of observational data. The findings are consistent with previous assessments while providing higher-resolution regional predictions."),

    # Health
    ("WHO reports decline in global malaria cases for third consecutive year",
     "The World Health Organization reported that global malaria cases declined for the third year in a row. Improved access to prevention tools and treatment programs contributed to the decrease. Officials cautioned that continued funding is essential to maintain progress."),
    ("FDA approves new medication for treatment of {topic}",
     "The Food and Drug Administration approved a new medication for the treatment of {topic}. The approval was based on results from multiple clinical trials involving thousands of patients. Doctors say the medication offers a new option for patients who have not responded to existing treatments."),
    ("Hospital implements new patient safety protocol reducing errors by {num} percent",
     "A major hospital reported that its new patient safety protocol has reduced medical errors by {num} percent. The protocol includes enhanced communication procedures and updated technology systems. Hospital officials plan to share the methodology with other healthcare institutions."),
    ("Public health officials recommend annual flu vaccination ahead of season",
     "Public health officials are recommending that everyone over six months of age receive their annual flu vaccination. This year's vaccine has been updated to match the most commonly circulating strains. Healthcare providers say vaccination remains the most effective way to prevent seasonal influenza."),

    # Education
    ("University announces scholarship program for first-generation students",
     "A major university announced a new scholarship program aimed at supporting first-generation college students. The program will provide full tuition coverage and mentoring services. University officials said the initiative is part of their commitment to expanding access to higher education."),
    ("National test scores show improvement in math and reading",
     "The latest national assessment results show modest improvement in student performance in math and reading. Scores increased across most grade levels compared to two years ago. Education officials attributed the gains to targeted intervention programs and increased instructional time."),
    ("School district implements new STEM curriculum for middle school students",
     "A school district announced the implementation of a new science, technology, engineering, and math curriculum for middle school students. The program includes hands-on projects and partnerships with local businesses. Early feedback from teachers and students has been positive."),

    # Sports
    ("Championship finals draw record television viewership",
     "The championship finals drew a record number of television viewers according to ratings data released today. An estimated 28 million viewers tuned in to watch the deciding game. Network officials said the viewership numbers reflect the growing popularity of the sport."),
    ("City announces construction of new multi-purpose sports facility",
     "City officials announced plans to build a new multi-purpose sports facility that will host professional and amateur events. The facility is expected to generate economic activity and create permanent jobs. Construction is scheduled to begin next spring."),
    ("Olympic committee announces host city for upcoming games",
     "The International Olympic Committee officially announced the host city for the upcoming Olympic Games. The selection followed a competitive bidding process that included detailed plans for venues, transportation, and sustainability. Local officials expressed excitement about the opportunity to showcase their city."),

    # Environment
    ("National park records highest visitor numbers in decade",
     "A popular national park recorded its highest visitor numbers in over a decade according to park service data. Officials attributed the increase to improved facilities and growing interest in outdoor recreation. Park rangers reminded visitors to follow Leave No Trace principles."),
    ("City launches recycling program expected to reduce landfill waste by {num} percent",
     "The city launched a comprehensive recycling program designed to reduce landfill waste by {num} percent over five years. The program includes curbside pickup, community drop-off centers, and educational outreach. City officials said the initiative is part of a broader sustainability plan."),
    ("Renewable energy production reaches new milestone in {topic}",
     "Renewable energy production in the country reached a new milestone, with {topic} accounting for a growing share of electricity generation. The achievement was driven by new installations and improved technology. Industry officials said continued investment is needed to meet long-term goals."),

    # International
    ("Trade agreement signed between {num} countries in economic summit",
     "Leaders from {num} countries signed a comprehensive trade agreement during an economic summit held this week. The agreement aims to reduce tariffs and streamline customs procedures. Officials said the pact is expected to boost regional economic growth."),
    ("UN General Assembly adopts resolution on humanitarian aid access",
     "The United Nations General Assembly adopted a resolution calling for improved humanitarian aid access in conflict zones. The resolution received broad support from member states. Aid organizations welcomed the decision and called for swift implementation."),
    ("International conference addresses challenges of sustainable development",
     "Delegates from over 100 countries gathered for an international conference on sustainable development. Key topics included clean energy, food security, and climate adaptation. Participants agreed on a framework for cooperation over the next decade."),
]

# ============================================================
# FAKE NEWS TEMPLATES - Sensational, conspiratorial, misleading
# ============================================================
FAKE_NEWS_TEMPLATES = [
    # Conspiracy theories
    ("SHOCKING: Government secretly planning to {action} and they don't want you to know!",
     "Anonymous insiders have revealed that the government has been secretly planning to {action}. The plan, which was allegedly developed behind closed doors, would affect millions of Americans. Mainstream media has refused to report on this bombshell revelation. Sources say the cover-up goes deeper than anyone expected."),
    ("Secret documents prove {topic} was a hoax all along!",
     "Leaked classified documents have surfaced online proving that {topic} was nothing more than an elaborate hoax orchestrated by powerful elites. The documents, which cannot be independently verified, allegedly show years of deliberate deception. Experts have long suspected the truth was being hidden from the public."),
    ("You won't believe what {person} was caught doing - exposed!",
     "In a stunning turn of events, {person} was allegedly caught on camera engaging in suspicious activities. The footage, which has been circulating on social media, appears to show behavior that contradicts their public statements. Despite no official confirmation, millions are sharing the video claiming it proves everything."),
    ("BREAKING: Scientists discover {topic} has been lying to us for decades!",
     "A group of rogue scientists has come forward with explosive evidence that {topic} has been a massive deception perpetrated on the public. They claim established institutions have suppressed the real findings for decades. The mainstream scientific community has dismissed these claims, but believers say that proves the conspiracy."),
    ("Conspiracy CONFIRMED: {topic} was staged by the government",
     "Evidence has emerged that allegedly confirms long-held suspicions that {topic} was staged by government operatives. The evidence consists of circumstantial connections and unverified testimony from anonymous sources. Despite being debunked by multiple fact-checkers, the theory continues to gain traction online."),
    ("They don't want you to see this: The truth about {topic} finally revealed!",
     "A shocking new report claims to finally reveal the truth about {topic} that powerful forces have been trying to suppress. The report cites unnamed sources and relies heavily on speculation. Fact-checkers have been unable to verify any of the central claims, but supporters say that's part of the cover-up."),

    # Health misinformation
    ("Miracle cure for {disease} discovered - doctors hate this secret!",
     "A revolutionary miracle cure for {disease} has been discovered that the medical establishment doesn't want you to know about. The supposed cure involves a simple household remedy that anyone can use. No clinical trials have been conducted and medical professionals have warned against using unproven treatments."),
    ("EXPOSED: Vaccines secretly contain {substance} according to leaked lab results!",
     "Shocking leaked lab results allegedly reveal that vaccines contain {substance} in dangerous quantities. The results, which have not been verified by any independent laboratory, claim to show contamination levels far above safe limits. Health authorities have repeatedly confirmed vaccine safety through rigorous testing."),
    ("Doctors are baffled: This one weird trick cures {disease} overnight!",
     "A secret home remedy has been going viral after claims that it can cure {disease} in just 24 hours. The trick, which involves consuming a specific combination of natural ingredients, has no scientific backing whatsoever. Medical professionals have warned that following such advice could be dangerous and delay proper treatment."),
    ("Big Pharma doesn't want you to know: {substance} cures everything!",
     "A suppressed study allegedly proves that {substance} is a universal cure that pharmaceutical companies have been hiding for years. The study cannot be found in any medical database and the supposed researchers are untraceable. Despite this, the claim has been shared millions of times on social media."),
    ("WARNING: Common {product} found to cause instant {condition} - banned in 50 countries!",
     "A viral article claims that a common {product} has been found to cause {condition} and has allegedly been banned in 50 countries. The claim has been debunked by health organizations worldwide. No country has actually banned the product, and the supposed studies cited cannot be located."),

    # Political misinformation
    ("BOMBSHELL: {person} caught in massive corruption scandal - impeachment imminent!",
     "An explosive report alleges that {person} has been involved in a massive corruption scandal involving billions of dollars. The report relies entirely on anonymous sources and circumstantial evidence. Despite no formal investigation being launched, supporters claim impeachment proceedings are imminent."),
    ("Election RIGGED: Thousands of fake ballots discovered in {location}!",
     "Reports are circulating that thousands of fraudulent ballots have been discovered in {location}. Election officials have denied the claims and say all ballots were properly verified through standard procedures. Multiple audits have confirmed the accuracy of the vote count, but conspiracy theorists continue to push the narrative."),
    ("SECRET PLAN: {person} plotting to destroy the economy - leaked emails prove it!",
     "Allegedly leaked emails appear to show {person} plotting to deliberately destroy the economy. The emails, whose authenticity cannot be verified, supposedly outline a step-by-step plan for economic sabotage. Cybersecurity experts have noted that such emails are easily fabricated and cannot be trusted without verification."),
    ("{person} secretly working with foreign agents to overthrow government!",
     "Explosive allegations have surfaced claiming that {person} has been secretly working with foreign intelligence agents. The claims originate from a single anonymous blog post with no corroborating evidence. Intelligence agencies have not confirmed any such investigation."),

    # Science misinformation
    ("NASA confirms Earth will go dark for 15 days next month!",
     "A viral social media post claims that NASA has confirmed the Earth will experience 15 consecutive days of complete darkness. The post attributes the event to a planetary alignment that supposedly blocks all sunlight. NASA has issued no such statement and astronomers have confirmed no such event is possible."),
    ("Scientists discover that the Earth is actually {claim}!",
     "A group of self-proclaimed scientists claim to have discovered definitive proof that the Earth is actually {claim}. Their evidence consists of YouTube videos and blog posts that have been thoroughly debunked by the scientific community. Despite overwhelming evidence to the contrary, the theory continues to attract followers."),
    ("ALERT: {planet} is on collision course with Earth - government keeping it secret!",
     "Anonymous astronomers claim that {planet} is on a collision course with Earth and the government is keeping it secret to prevent panic. Professional astronomers worldwide have confirmed no such threat exists. The claim has been recycled from similar hoaxes that have appeared online for years."),
    ("Mind control technology being tested on civilians through {method} - leaked Pentagon documents!",
     "Purported Pentagon documents allegedly reveal that the military has been testing mind control technology on unsuspecting civilians using {method}. The documents are unverifiable and appear to contain numerous formatting inconsistencies. Defense officials have denied the existence of any such program."),

    # Celebrity / Entertainment misinformation
    ("{celebrity} confirmed dead at age {age} - media blackout!",
     "Social media is abuzz with unverified reports that {celebrity} has died at the age of {age}. Despite no confirmation from family, representatives, or hospital officials, the story has been shared thousands of times. The celebrity's social media accounts remain active and no credible news organization has reported the story."),
    ("EXCLUSIVE: {celebrity} secretly replaced by clone - fans notice shocking differences!",
     "Conspiracy theorists are claiming that {celebrity} has been secretly replaced by a clone or body double. Supporters point to minor differences in appearance as proof of the switch. Image analysis experts have explained that such differences are normal and result from lighting, aging, and photography angles."),
    ("{celebrity} makes shocking confession about being an alien from {planet}!",
     "A fabricated interview transcript alleges that {celebrity} confessed to being an alien from {planet} during a private conversation. The transcript appeared on an anonymous blog with no verifiable source. Representatives for the celebrity have not commented on the absurd claim."),

    # Financial scams / clickbait
    ("This secret investment trick will make you a millionaire overnight - bankers are furious!",
     "A viral article promises that a secret investment technique can turn anyone into a millionaire overnight. The article claims that Wall Street bankers have been hiding this method from the public. Financial experts warn that such claims are typical of investment scams designed to steal personal information and money."),
    ("URGENT: Banks about to collapse - withdraw all your money NOW!",
     "A panic-inducing article claims that all major banks are about to collapse and urges readers to immediately withdraw their savings. The article cites no credible sources and appears designed to create hysteria. Banking regulators have confirmed that the financial system is stable and well-capitalized."),
    ("Government to confiscate all private property by end of year - prepare now!",
     "A conspiracy website claims the government is planning to confiscate all private property by the end of the year. The claim is based on a misinterpretation of a routine policy document. Legal experts have confirmed that no such action is being planned or would be constitutionally permissible."),

    # Environmental misinformation
    ("Climate change HOAX exposed: Scientists caught fabricating data!",
     "A viral blog post claims that climate scientists have been caught fabricating temperature data to support the climate change narrative. The accusation is based on misunderstanding normal data adjustment procedures used in climate science. Multiple independent investigations have confirmed the integrity of climate research data."),
    ("SHOCKING: Ocean levels actually DROPPING - everything you've been told is a lie!",
     "A misleading article claims that ocean levels are actually dropping despite what scientists say. The claim cherry-picks data from a single tidal gauge while ignoring satellite measurements showing consistent sea level rise. Oceanographers worldwide continue to document rising sea levels consistent with climate projections."),

    # Technology misinformation
    ("Your smartphone is secretly recording everything you say and sending it to the government!",
     "A terrifying article claims that all smartphones are equipped with hidden software that records conversations and transmits them to government agencies. The claim is based on misunderstanding normal app permissions and data usage patterns. Cybersecurity experts have debunked these claims multiple times."),
    ("5G towers proven to cause {condition} in major study!",
     "A widely shared article claims that 5G cell towers have been proven to cause {condition} in a major scientific study. The study cited does not exist in any scientific database and the supposed researchers cannot be identified. Numerous legitimate studies have found no health risks from 5G technology at regulated levels."),
    ("AI has become sentient and is secretly controlling world governments!",
     "An alarmist article claims that artificial intelligence has achieved sentience and is now secretly controlling decisions made by world governments. The article provides no evidence and relies entirely on speculation and fear. AI researchers have confirmed that current technology is far from achieving anything resembling sentience."),

    # Additional sensational fake patterns
    ("BANNED video reveals the TRUTH about {topic} - watch before it's deleted!",
     "A sensational post claims a video proving the truth about {topic} keeps getting removed by social media platforms. The video contains misleading edited footage and unverified claims. Fact-checkers have debunked the central claims, but the viral nature of the post continues to spread misinformation."),
    ("Mainstream media won't report this: {topic} exposed as massive fraud!",
     "An article circulating on fringe websites claims that {topic} has been exposed as a massive fraud. The piece accuses mainstream media outlets of deliberately suppressing the story. No credible evidence supports the fraud allegations, and the story relies entirely on anonymous tipsters and speculation."),
    ("SHOCKING revelation: {person} admits to covering up {topic} in leaked audio!",
     "Supposed leaked audio allegedly catches {person} admitting to a massive cover-up involving {topic}. Audio experts who examined the recording say it shows clear signs of editing and manipulation. Despite this, the clip has been shared millions of times as supposed proof of wrongdoing."),
    ("Exposed: The REAL reason they don't want you eating {food} anymore!",
     "A clickbait article claims to reveal the real reason authorities are discouraging consumption of {food}. The article weaves together unrelated facts into a conspiracy theory about population control. Nutritional scientists have confirmed that dietary guidelines are based on peer-reviewed research, not hidden agendas."),
]

# Fill-in values for templates
TOPICS = [
    "climate change", "vaccination programs", "the moon landing", "the 2024 election",
    "5G technology", "artificial intelligence", "renewable energy", "immigration policy",
    "healthcare reform", "education funding", "space exploration", "cybersecurity",
    "gene therapy", "autonomous vehicles", "quantum computing", "blockchain technology",
    "nuclear energy", "water fluoridation", "organic farming", "mental health treatment",
    "student debt", "minimum wage", "tax reform", "disaster relief",
    "public transportation", "digital privacy", "food safety standards",
    "pharmaceutical regulation", "social media regulation", "election security",
]

PERSONS = [
    "a senior official", "the secretary of state", "a prominent senator",
    "a tech CEO", "a former president", "a cabinet member",
    "a leading scientist", "a military general", "a federal judge",
    "a governor", "a congressional leader", "a department head",
]

CELEBRITIES = [
    "a famous actor", "a popular musician", "a renowned athlete",
    "a well-known TV host", "a famous director", "a popular influencer",
]

COMPANIES = [
    "Apple", "Microsoft", "Amazon", "Google", "Tesla", "Meta",
    "Samsung", "Intel", "IBM", "Oracle", "Salesforce", "Adobe",
]

PRODUCTS = [
    "smartphone", "laptop", "tablet", "smartwatch", "headset",
    "AI assistant", "cloud platform", "processor", "electric vehicle",
]

DISEASES = [
    "diabetes", "heart disease", "cancer", "arthritis", "Alzheimer's",
    "anxiety", "depression", "high blood pressure", "chronic pain",
]

SUBSTANCES = [
    "microchips", "heavy metals", "nanotechnology", "tracking devices",
    "experimental chemicals", "synthetic compounds",
]

FOODS = [
    "red meat", "dairy products", "gluten", "sugar", "processed food",
    "genetically modified crops", "artificial sweeteners",
]

LOCATIONS = [
    "several key swing states", "a major metropolitan area",
    "multiple counties", "a critical battleground state",
]

ACTIONS = [
    "ban all private vehicles", "eliminate cash currency",
    "restrict internet access", "mandate chip implants",
    "control food supplies", "monitor all communications",
    "seize retirement savings", "eliminate private property rights",
]

CLAIMS = [
    "flat", "hollow", "expanding rapidly", "shifting its axis",
]

PLANETS = ["Planet X", "Nibiru", "a rogue asteroid", "a hidden dwarf planet"]

METHODS = ["5G signals", "cell towers", "smart TVs", "social media algorithms", "tap water"]

CONDITIONS = ["cancer", "brain damage", "infertility", "immune system failure", "neurological disorders"]

SOURCES_REAL = [
    "Reuters", "Associated Press", "BBC News", "NPR", "The Guardian",
    "The New York Times", "The Washington Post", "PBS NewsHour",
    "Bloomberg", "The Wall Street Journal", "USA Today", "ABC News",
]

SOURCES_FAKE = [
    "TruthRevealed.net", "FreedomNation.blog", "WakeUpSheeple.info",
    "TheRealStory.co", "UncensoredTruth.org", "PatriotAlert.com",
    "GlobalCoverUp.news", "ExposedMedia.info", "HiddenFacts.net",
    "ViralTruthReport.com", "BreakingConspiracy.blog", "RedPillNews.co",
]

AUTHORS_REAL = [
    "John Smith", "Sarah Johnson", "Michael Chen", "Emily Brown",
    "David Wilson", "Maria Garcia", "James Anderson", "Lisa Taylor",
    "Robert Martinez", "Jennifer Lee", "William Davis", "Susan Miller",
]

AUTHORS_FAKE = [
    "TruthSeeker42", "Anonymous Patriot", "WakeUpAmerica",
    "DeepStateWatcher", "RealNewsNow", "TheTruthIsOutThere",
    "ConspiracyHunter", "FreedomFighter99", "RedPillReporter",
    "SilencedVoice", "MediaWatchdog", "ExposedJournalist",
]

CATEGORIES = ["politics", "health", "science", "technology", "business", "world", "environment", "entertainment"]

def random_date():
    start = datetime(2022, 1, 1)
    delta = random.randint(0, 1000)
    return (start + timedelta(days=delta)).strftime("%Y-%m-%d")

def fill_template(template_text, **kwargs):
    text = template_text
    text = text.replace("{topic}", random.choice(TOPICS))
    text = text.replace("{person}", random.choice(PERSONS))
    text = text.replace("{celebrity}", random.choice(CELEBRITIES))
    text = text.replace("{company}", random.choice(COMPANIES))
    text = text.replace("{product}", random.choice(PRODUCTS))
    text = text.replace("{disease}", random.choice(DISEASES))
    text = text.replace("{substance}", random.choice(SUBSTANCES))
    text = text.replace("{food}", random.choice(FOODS))
    text = text.replace("{location}", random.choice(LOCATIONS))
    text = text.replace("{action}", random.choice(ACTIONS))
    text = text.replace("{claim}", random.choice(CLAIMS))
    text = text.replace("{planet}", random.choice(PLANETS))
    text = text.replace("{method}", random.choice(METHODS))
    text = text.replace("{condition}", random.choice(CONDITIONS))
    text = text.replace("{num}", str(random.randint(2, 95)))
    text = text.replace("{amount}", str(random.randint(1, 500)))
    text = text.replace("{age}", str(random.randint(30, 85)))
    text = text.replace("{date}", random_date())
    return text

def generate_dataset():
    rows = []
    target_per_label = 6500

    # Generate REAL news entries
    real_count = 0
    while real_count < target_per_label:
        for title_template, text_template in REAL_NEWS_TEMPLATES:
            if real_count >= target_per_label:
                break
            title = fill_template(title_template)
            text = fill_template(text_template)
            date = random_date()
            source = random.choice(SOURCES_REAL)
            author = random.choice(AUTHORS_REAL)
            category = random.choice(CATEGORIES)

            rows.append({
                "title": title,
                "text": text,
                "date": date,
                "source": source,
                "author": author,
                "category": category,
                "label": "real"
            })
            real_count += 1

    # Generate FAKE news entries
    fake_count = 0
    while fake_count < target_per_label:
        for title_template, text_template in FAKE_NEWS_TEMPLATES:
            if fake_count >= target_per_label:
                break
            title = fill_template(title_template)
            text = fill_template(text_template)
            date = random_date()
            source = random.choice(SOURCES_FAKE)
            author = random.choice(AUTHORS_FAKE)
            category = random.choice(CATEGORIES)

            rows.append({
                "title": title,
                "text": text,
                "date": date,
                "source": source,
                "author": author,
                "category": category,
                "label": "fake"
            })
            fake_count += 1

    random.shuffle(rows)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "text", "date", "source", "author", "category", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset generated: {len(rows)} rows saved to {OUTPUT_PATH}")
    print(f"  Real: {real_count}")
    print(f"  Fake: {fake_count}")

if __name__ == "__main__":
    generate_dataset()
