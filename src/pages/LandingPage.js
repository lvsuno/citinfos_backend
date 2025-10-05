import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LocationOnOutlined,
  PeopleOutlined,
  TrendingUpOutlined,
  ChatBubbleOutlined,
  EventOutlined,
  BusinessOutlined,
  AutoAwesomeOutlined,
  ArrowForwardOutlined,
  PlayArrowOutlined,
  YouTube as YouTubeIcon
} from '@mui/icons-material';
import { Container, Row, Col, Button, Card } from 'react-bootstrap';
import styles from './LandingPage.module.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const heroRef = useRef(null);
  const featuresRef = useRef(null);

  useEffect(() => {
    setIsVisible(true);

    const handleMouseMove = (e) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleGetStarted = () => {
    navigate('/signup');
  };

  const handleWatchDemo = () => {
    window.open('https://www.youtube.com/', '_blank');
  };

  const features = [
    {
      icon: <LocationOnOutlined className={styles.featureIcon} />,
      title: "Connectez votre municipalité",
      description: "Découvrez ta municipalité comme jamais auparavant",
      color: "#06B6D4"
    },
    {
      icon: <PeopleOutlined className={styles.featureIcon} />,
      title: "Communauté active",
      description: "Rejoignez des milliers de citoyens engagés dans leur région",
      color: "#84CC16"
    },
    {
      icon: <ChatBubbleOutlined className={styles.featureIcon} />,
      title: "Discussions enrichissantes",
      description: "Partagez vos idées et participez aux débats locaux",
      color: "#06B6D4"
    },
    {
      icon: <EventOutlined className={styles.featureIcon} />,
      title: "Événements locaux",
      description: "Ne manquez plus aucun événement de votre ville",
      color: "#84CC16"
    },
    {
      icon: <BusinessOutlined className={styles.featureIcon} />,
      title: "Développement économique",
      description: "Contribuez à la croissance de votre communauté",
      color: "#06B6D4"
    },
    {
      icon: <TrendingUpOutlined className={styles.featureIcon} />,
      title: "Impact positif",
      description: "Mesurez et amplifiez votre contribution locale",
      color: "#84CC16"
    }
  ];

  return (
    <div className={styles.landingPage}>
      {/* Arrière-plan animé */}
      <div
        className={styles.animatedBackground}
        style={{
          background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(6, 182, 212, 0.1) 0%, rgba(132, 204, 22, 0.05) 50%, transparent 100%)`
        }}
      />

      {/* Particules flottantes */}
      <div className={styles.particles}>
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className={styles.particle}
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 20}s`,
              animationDuration: `${15 + Math.random() * 10}s`
            }}
          />
        ))}
      </div>

      {/* Section Hero */}
      <section className={styles.hero} ref={heroRef}>
        <Container fluid className="h-100">
          <Row className="h-100 align-items-center justify-content-center">
            <Col lg={10} xl={8}>
              <div className={`${styles.heroContent} ${isVisible ? styles.visible : ''}`}>
                <div className={styles.heroBadge}>
                  <AutoAwesomeOutlined className={styles.badgeIcon} />
                  <span>La voix de votre communauté</span>
                </div>

                <h1 className={styles.heroTitle}>
                  La parole à tout le monde dans votre
                  <span className={styles.gradientText}> municipalité</span>
                </h1>

                <p className={styles.heroSubtitle}>
                  Notre mission est de connecter les citoyens du même endroit pour contribuer ensemble au développement économique, social et culturel de leur région. Rejoignez  communauté qui façonne l'avenir.
                </p>

                <div className={styles.heroButtons}>
                  <Button
                    className={styles.primaryButton}
                    onClick={handleWatchDemo}
                    size="lg"
                  >
                    <YouTubeIcon className={styles.buttonIcon} />
                    <span>Voir démo</span>
                  </Button>

                  <Button
                    variant="outline-light"
                    className={styles.secondaryButton}
                    onClick={() => navigate('/signup')}
                    size="lg"
                  >
                    <PlayArrowOutlined className={styles.buttonIcon} />
                    <span>Rejoindre maintenant</span>
                  </Button>
                </div>

                <div className={styles.heroStats}>
                  <div className={styles.stat}>
                    <div className={styles.statNumber}>2</div>
                    <div className={styles.statLabel}>Municipalités</div>
                  </div>
                  <div className={styles.statDivider} />
                  <div className={styles.stat}>
                    <div className={styles.statNumber}>3</div>
                    <div className={styles.statLabel}>Citoyens connectés</div>
                  </div>
                  <div className={styles.statDivider} />
                  <div className={styles.stat}>
                    <div className={styles.statNumber}>∞</div>
                    <div className={styles.statLabel}>Possibilités</div>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Section Fonctionnalités */}
      <section className={styles.features} ref={featuresRef}>
        <Container>
          <Row>
            <Col lg={12} className="text-center mb-5">
              <div className={styles.sectionBadge}>
                <span>Fonctionnalités</span>
              </div>
              <h2 className={styles.sectionTitle}>
                Une plateforme pensée pour
                <span className={styles.gradientText}> votre communauté</span>
              </h2>
              <p className={styles.sectionSubtitle}>
                Découvrez tous les outils dont vous avez besoin pour vous impliquer et faire la différence
              </p>
            </Col>
          </Row>

          <Row>
            {features.map((feature, index) => (
              <Col lg={4} md={6} key={index} className="mb-4">
                <Card
                  className={`${styles.featureCard} ${isVisible ? styles.visible : ''}`}
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <Card.Body className={styles.featureBody}>
                    <div
                      className={styles.featureIconWrapper}
                      style={{ backgroundColor: `${feature.color}15`, color: feature.color }}
                    >
                      {feature.icon}
                    </div>
                    <h3 className={styles.featureTitle}>{feature.title}</h3>
                    <p className={styles.featureDescription}>{feature.description}</p>
                    <div className={styles.featureArrow} style={{ color: feature.color }}>
                      <ArrowForwardOutlined />
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        </Container>
      </section>

      {/* Section CTA Final */}
      <section className={styles.finalCTA}>
        <Container>
          <Row>
            <Col lg={8} className="mx-auto text-center">
              <div className={styles.ctaContent}>
                <h2 className={styles.ctaTitle}>
                  Prêt à faire partie du changement ?
                </h2>
                <p className={styles.ctaSubtitle}>
                  Rejoignez dès aujourd'hui des milliers de citoyens qui construisent l'avenir de leur municipalité
                </p>
                <Button
                  className={styles.ctaButton}
                  onClick={handleGetStarted}
                  size="lg"
                >
                  <span>Commencer l'aventure</span>
                  <AutoAwesomeOutlined className={styles.buttonIcon} />
                </Button>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Pied de page */}
      <footer className={styles.footer}>
        <Container>
          <Row>
            <Col className="text-center">
              <p className={styles.footerText}>
                © 2025 Communauté. Connecter • Contribuer • Construire l'avenir ensemble
              </p>
            </Col>
          </Row>
        </Container>
      </footer>
    </div>
  );
};

export default LandingPage;