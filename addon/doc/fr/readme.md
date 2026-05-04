<p align="center">
  <img src="https://www.nvaccess.org/wp-content/uploads/2015/11/NVDA_logo_blue_600px.png" alt="NVDA Logo" width="120">
</p>

<br>

# <p align="center">DoctorNVDA</p>

<br>

<p align="center">Le compagnon ultime de diagnostic et de récupération pour les utilisateurs de NVDA, transformant la façon dont vous entretenez la santé de votre lecteur d'écran.</p>

<br>

<p align="center">
  <b>author:</b> chai chaimee
</p>

<p align="center">
  <b>url:</b> <a href="https://github.com/chaichaimee/DoctorNVDA">https://github.com/chaichaimee/DoctorNVDA</a>
</p>

---

<br>

## <p align="center">Description</p>

<br>

Votre NVDA vous semble-t-il lent ? Des erreurs étranges apparaissent-elles après l'installation de nouvelles extensions ? **DoctorNVDA** agit comme un médecin personnel pour votre logiciel. Il fournit des outils de haute précision pour diagnostiquer les conflits et restaurer la santé instantanément, garantissant que vous ne perdiez jamais votre configuration ni votre temps.

<br>

Cette extension est conçue pour chaque utilisateur, quel que soit son niveau technique. Elle simplifie les dépannages complexes en quelques clics, vous permettant de gérer les sauvegardes, d'identifier les extensions problématiques et d'effectuer des redémarrages d'urgence sans jamais avoir besoin de toucher à des fichiers système compliqués ou au Gestionnaire des tâches de Windows.

<br>

## <p align="center">Raccourcis Clavier</p>

<br>

DoctorNVDA utilise un système intelligent de **Multi-frappe**. Cela signifie que vous n'avez besoin de retenir qu'une seule combinaison de touches principale pour effectuer plusieurs actions de récupération.

<br>

> **Commande Principale : ALT + Windows + D**
>
> *   **Appui simple :** Ouvre le **Menu Principal de DoctorNVDA** pour accéder à toutes les fonctionnalités.
>
> *   **Double appui :** **Redémarre NVDA** instantanément (Mode Normal).
>
> *   **Triple appui :** **Redémarrage d'urgence avec extensions désactivées** (Mode Sans Échec).

<br>

## <p align="center">Fonctionnalités</p>

<br>

### 1. Débogage par recherche binaire (Le détective d'extensions)

<br>

Trouver une seule extension défectueuse parmi des dizaines, c'est comme chercher une aiguille dans une botte de foin. Cette fonctionnalité automatise la méthode de "recherche binaire" pour trouver le coupable à votre place.

<br>

**Guide étape par étape :**
1. Lancez le diagnostic depuis le menu DoctorNVDA.
2. NVDA redémarrera avec la moitié de vos extensions désactivées.
3. Un dialogue demandera : **"Le problème a-t-il DISPARU ?"**
4. Si vous répondez **Oui**, le détective sait que le problème est dans la moitié désactivée. Si **Non**, il est dans la moitié active.
5. Le processus se répète, réduisant le groupe jusqu'à ce que l'extension problématique exacte soit isolée.

<br>

### 2. Créer & Restaurer les paramètres NVDA (Machine à remonter le temps)

<br>

Protégez vos dictionnaires personnalisés, vos gestes et vos profils. Cette fonctionnalité crée un **"Point de récupération"** auquel vous pouvez revenir à tout moment.

<br>

**Guide étape par étape :**
1. **Pour sauvegarder :** Sélectionnez "Créer une récupération" quand votre NVDA fonctionne parfaitement.
2. **Pour restaurer :** Si vos paramètres sont corrompus, sélectionnez "Restaurer les paramètres NVDA" dans le menu.
3. Choisissez une date de récupération dans la liste.
4. DoctorNVDA remplacera automatiquement les fichiers corrompus et redémarrera NVDA pour vous.

<br>

### 3. Résumé des infos système

<br>

Besoin de signaler un bug ou de vérifier la santé de votre système ? Cet outil rassemble toutes les statistiques vitales en un seul endroit — aucune connaissance technique requise.

<br>

**Guide étape par étape :**
1. Sélectionnez "Résumé des infos système" dans le menu.
2. Un rapport clair apparaîtra affichant votre version de NVDA, votre version de Windows et l'architecture du système.
3. Ces infos sont automatiquement formatées pour être faciles à lire et à partager avec les développeurs ou les équipes de support.

<br>

### 4. Accès instantané à la config utilisateur

<br>

Évitez de fouiller dans les dossiers cachés de Windows. Accédez directement à l'endroit où NVDA stocke vos paramètres.

<br>

```text
%APPDATA%\nvda