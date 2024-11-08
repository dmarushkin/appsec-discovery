package models;

import javax.persistence.Basic;
import javax.persistence.Entity;
import javax.persistence.Id;

@Entity
@javax.persistence.Table(name = "audio", schema = "fingerprint", catalog = "")
public class AudioEntity {

    private int counter;

    @Id
    @javax.persistence.Column(name = "counter")
    public int getCounter() {
        return counter;
    }

    public void setCounter(int counter) {
        this.counter = counter;
    }

    private String id;

    @Basic
    @javax.persistence.Column(name = "id")
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    private String acSampleRate;

    @Basic
    @Column(name = "acSampleRate")
    public String getAcSampleRate() {
        return acSampleRate;
    }

    public void setAcSampleRate(String acSampleRate) {
        this.acSampleRate = acSampleRate;
    }

    private String acState;

    @Basic
    @javax.persistence.Column(name = "acState")
    public String getAcState() {
        return acState;
    }

}