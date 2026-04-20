# Spécifications du Projet : Chatbot E-commerce

## 1. Objectif du Projet
Un site marchand souhaite automatiser son support client. Le but est de concevoir un chatbot capable de répondre efficacement aux questions des clients concernant les livraisons, les commandes, et autres requêtes courantes.

## 2. Concepts Techniques Clés
* **RAG métier :** Génération augmentée par la recherche sur les données de l'entreprise.
* **API :** Connexion à des services externes pour le suivi des commandes.
* **Prompt engineering :** Optimisation des requêtes au modèle de langage.

## 3. Étapes de Réalisation
1.  **Collecte des données :** Rassembler la FAQ et les Conditions Générales de Vente (CGV).
2.  **Indexation :** Traiter et vectoriser les données documentaires.
3.  **Implémentation RAG :** Mettre en place le système de récupération et de génération.
4.  **Connexion API :** Intégrer les appels dynamiques pour les statuts de commandes.
5.  **Personnalisation du ton :** Ajuster le persona du chatbot.
6.  **Interface web :** Développer l'interface utilisateur.
7.  **Déploiement :** Conteneuriser avec Docker, de manière structurée pour s'aligner avec les bonnes pratiques DevOps.

## 4. Livrables Attendus
* Un chatbot fonctionnel et opérationnel.
* Un jeu de cas de test clients validés.
* Un rapport final au format PDF détaillant l'architecture et les choix techniques.

---

## 5. Cas de Test et Exemples de Questions

### Catégorie 1 : Commandes & Suivi

**Questions Simples (Réponse Directe)**
| Question client | Intention | Données nécessaires |
| :--- | :--- | :--- |
| « Où en est ma commande n°12345 ? » | Suivi de commande | Numéro de commande, statut, transporteur |
| « Quand vais-je recevoir ma commande ? » | Date de livraison estimée | Adresse, méthode d'expédition, délai moyen |
| « Puis-je modifier ma commande après validation ? » / « Comment annuler ma commande ? » | Modification post-achat / Annulation | Délai de traitement, statut de préparation, Délai d'annulation, procédure, remboursement |
| « Je n'ai pas reçu de confirmation de commande » | Problème de notification | Email client, statut de la commande, logs d'envoi |

**Questions Complexes (Multi-Étapes)**
| Question client | Défi pour le chatbot | Réponse attendue |
| :--- | :--- | :--- |
| « J'ai commandé 3 articles mais je n'en ai reçu que 2 » / « Ma commande est marquée "livrée" mais je ne l'ai pas reçue » | Gestion de commande partiellement livrée / Gestion de litige logistique | Vérifier le statut de chaque ligne, expliquer les expéditions fractionnées, proposer un suivi ou un remboursement. Proposer une enquête transporteur, vérifier l'adresse, offrir un geste commercial si nécessaire |
| « Puis-je ajouter un article à une commande déjà passée ? » | Fusion de commandes | Expliquer les limites techniques, proposer une nouvelle commande avec livraison groupée si possible |

### Catégorie 2 : Livraison & Expédition

**Questions Simples**
| Question client | Intention | Données nécessaires |
| :--- | :--- | :--- |
| « Quels sont les délais de livraison ? » | Information générale | Zone géographique, mode d'expédition |
| « Livrez-vous en Corse / DOM-TOM ? » | Couverture géographique | Zones desservies, surcoûts éventuels |
| « Puis-je choisir le jour de livraison ? » | Options de livraison | Disponibilités transporteur, options premium |
| « Combien coûtent les frais de port ? » | Tarification livraison | Panier moyen, zone, poids, promotions en cours |
| « Proposez-vous la livraison en point relais ? » | Modes de livraison | Réseau de partenaires, localisation du client |

**Questions Complexes**
| Question client | Défi pour le chatbot | Réponse attendue |
| :--- | :--- | :--- |
| « Je serai absent le jour de la livraison, que faire ? » / « Mon colis a été livré chez un voisin, comment le récupérer ? » / « La livraison est en retard par rapport à la date promise » | Gestion d'imprévu client / Litige de livraison / Gestion d'insatisfaction | Proposer report, livraison en point relais, ou autorisation de dépôt. Fournir les coordonnées du voisin (si autorisé) ou ouvrir un ticket transporteur. S'excuser, expliquer la cause, proposer compensation ou suivi prioritaire |

### Catégorie 3 : Paiement & Facturation

**Questions Simples**
| Question client | Intention | Données nécessaires |
| :--- | :--- | :--- |
| « Quels moyens de paiement acceptez-vous ? » | Information paiement | Liste des moyens (CB, PayPal, virement, etc.) |
| « Mon paiement a été refusé, pourquoi ? » | Problème de transaction | Logs de paiement, raisons courantes (plafond, solde, sécurité) |
| « Puis-je payer en plusieurs fois ? » | Options de paiement | Éligibilité client, partenaires de financement |
| « Où trouver ma facture ? » | Accès documentaire | Espace client, historique de commandes, envoi par email |
| « Le montant prélevé ne correspond pas à ma commande » | Litige de facturation | Détail de la commande, frais appliqués, historique des transactions |

**Questions Complexes**
| Question client | Défi pour le chatbot | Réponse attendue |
| :--- | :--- | :--- |
| « J'ai été débité deux fois pour la même commande » / « Je veux utiliser un code promo mais il ne fonctionne pas » / « Puis-je changer mon moyen de paiement après validation ? » | Gestion de double prélèvement / Gestion de promotion / Modification post-paiement | Vérifier les transactions, initier un remboursement si confirmé, rassurer le client. Vérifier validité, conditions d'éligibilité, proposer une alternative si possible. Expliquer les contraintes de sécurité, proposer annulation + nouvelle commande si nécessaire |

### Catégorie 4 : Retours, Échanges & Remboursements

**Questions Simples**
| Question client | Intention | Données nécessaires |
| :--- | :--- | :--- |
| « Comment retourner un article ? » | Procédure de retour | Politique de retour, étiquette prépayée, points de dépôt |
| « Sous quel délai puis-je retourner un produit ? » | Conditions de retour | Délai légal et commercial, état requis du produit |
| « Qui paie les frais de retour ? » | Prise en charge logistique | Politique selon motif (défaut, changement d'avis, erreur) |
| « Quand serai-je remboursé ? » | Délai de remboursement | Méthode de paiement initiale, délais bancaires, traitement interne |
| « Puis-je échanger un article contre une autre taille ? » | Échange produit | Stock disponible, procédure d'échange vs retour + nouvelle commande |